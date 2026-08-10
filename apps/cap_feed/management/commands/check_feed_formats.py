import asyncio
import time
import xml.etree.ElementTree as ET

import httpx
import validators
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Exists, Max, OuterRef
from django.utils import timezone

from apps.cap_feed.formats.utils import COMMON_REQUESTS_HEADERS, find_cap_link
from apps.cap_feed.models import Alert, Feed, ProcessedAlert

# Namespaces used to navigate the feed index documents.
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'cap': 'urn:oasis:names:tc:emergency:cap:1.2',
}

# CAP namespace prefix (version agnostic) used to validate individual alert docs.
CAP_NS_PREFIX = 'urn:oasis:names:tc:emergency:cap'

# Width of the single-line progress indicator; wide enough for the verdict breakdown.
PROGRESS_WIDTH = 110

# How many slowest feeds the response-time summary lists.
SLOWEST_COUNT = 5

# Root structure -> feed formats that are able to parse it.
STRUCTURE_TO_FORMATS = {
    'rss': {Feed.Format.RSS},
    'atom': {Feed.Format.ATOM, Feed.Format.NWS_US},
}


class Verdict:
    OK = 'OK'
    MISMATCH = 'MISMATCH'
    EMPTY = 'EMPTY'
    UNREACHABLE = 'UNREACHABLE'
    INVALID_XML = 'INVALID_XML'
    UNKNOWN_STRUCTURE = 'UNKNOWN_STRUCTURE'
    NOT_INGESTED = 'NOT_INGESTED'


def format_seconds(seconds: float) -> str:
    """Format a duration for the report, keeping sub-second timings readable."""
    if seconds < 1:
        return f'{seconds * 1000:.0f}ms'
    return f'{seconds:.2f}s'


def local_tag(tag: str) -> str:
    """Return the namespace-stripped, lower-cased local name of an XML tag."""
    if '}' in tag:
        tag = tag.split('}', 1)[1]
    return tag.lower()


def detect_structure(root: ET.Element) -> str:
    """Detect the feed index structure from its root element."""
    tag = local_tag(root.tag)
    if tag == 'rss':
        return 'rss'
    if tag == 'feed':
        # Atom family: covers both `atom` and `nws_us` (NWS is an Atom variant).
        return 'atom'
    return 'unknown'


def count_entries(root: ET.Element, fmt: str) -> int:
    """Count alert entries the *configured* parser would discover in the index."""
    if fmt == Feed.Format.RSS:
        channel = root.find('channel')
        if channel is None:
            return 0
        return len(channel.findall('item'))
    # atom / nws_us both iterate over atom:entry
    return len(root.findall('atom:entry', NS))


def first_alert_link(root: ET.Element, fmt: str) -> str | None:
    """Extract the first alert's document URL, mirroring the real parsers."""
    if fmt == Feed.Format.RSS:
        channel = root.find('channel')
        if channel is None:
            return None
        item = channel.find('item')
        link = item.find('link') if item is not None else None
        return link.text if link is not None else None

    entry = root.find('atom:entry', NS)
    if entry is None:
        return None
    if fmt == Feed.Format.NWS_US:
        return find_cap_link(entry, NS)
    # Plain atom: the <id> is the CAP doc URL.
    id_el = entry.find('atom:id', NS)
    return id_el.text if id_el is not None else None


def requires_cap_link(root: ET.Element) -> bool:
    """Whether this atom feed can only be read by following an <atom:link>.

    Both atom-family formats iterate over <atom:entry>, so the root element cannot
    tell them apart. `atom` reads the CAP document straight from <id>, which only
    works when <id> is a url; a bare urn or token leaves `nws_us` as the sole option.

    The reverse does not hold: a url-shaped <id> may still address something other
    than the CAP document (NWS ids resolve to a json resource, with CAP one suffix
    away), so a false result means undetermined rather than `atom`.
    """
    entry = root.find('atom:entry', NS)
    if entry is None:
        return False
    id_el = entry.find('atom:id', NS)
    return id_el is None or not id_el.text or not validators.url(id_el.text)


class Command(BaseCommand):
    help = (
        'Check that each feed\'s configured `format` matches the structure actually served, '
        'plus reachability / well-formedness / non-empty checks and whether any alerts are '
        'stored in the database. Feeds are fetched in parallel. Read-only; does not modify feeds.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'feed_ids',
            nargs='*',
            type=int,
            help='Optional feed IDs to check. If omitted, all feeds (matching other filters) are checked.',
        )
        parser.add_argument('--iso3', help='Only check feeds whose country iso3 matches (case-insensitive).')
        parser.add_argument('--url', help='Only check feeds whose url contains this substring.')
        parser.add_argument(
            '--format',
            choices=[f.value for f in Feed.Format],
            help='Only check feeds configured with this format.',
        )
        parser.add_argument(
            '--include-archived',
            action='store_true',
            help='Include archived feeds (excluded by default).',
        )
        parser.add_argument(
            '--deep',
            action='store_true',
            help='Also fetch the first alert document per feed and verify it is a CAP XML.',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Per-request timeout in seconds (default: 60).',
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=10,
            help='Number of feeds fetched in parallel (default: 10).',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Exit with an error if any feed has a problem (useful for CI).',
        )
        parser.add_argument(
            '--only-issues',
            action='store_true',
            help='Only print feeds with a non-OK verdict.',
        )
        parser.add_argument(
            '--skip-db',
            action='store_true',
            help='Skip the check for alerts stored in the database.',
        )

    def get_queryset(self, options):
        qs = Feed.objects.select_related('country').annotate(
            has_alerts=Exists(Alert.objects.filter(feed=OuterRef('pk'))),
            has_processed_alerts=Exists(ProcessedAlert.objects.filter(feed=OuterRef('pk'))),
        )
        if not options['include_archived']:
            qs = qs.filter(is_archived=False)
        if options['feed_ids']:
            qs = qs.filter(pk__in=options['feed_ids'])
        if options['iso3']:
            qs = qs.filter(country__iso3__iexact=options['iso3'])
        if options['url']:
            qs = qs.filter(url__icontains=options['url'])
        if options['format']:
            qs = qs.filter(format=options['format'])
        return qs.order_by('pk')

    def get_latest_sent(self, feeds):
        """Map feed id -> the `sent` of its most recent unexpired alert, in a single query.

        Restricted to unexpired alerts so the `cap_feed_alert_not_expired_idx` partial
        index carries the query, making its cost track the alerts still live rather than
        the size of the alert table. Expired alerts have no index to serve this and would
        turn it into a full scan.

        Grouping once over every feed also beats a per-feed correlated subquery: with no
        index on (feed_id, sent), each of those would sort that feed's alerts.
        """
        rows = (
            Alert.objects.filter(feed__in=[feed.pk for feed in feeds], is_expired=False)
            .values('feed_id')
            .annotate(latest_sent=Max('sent'))
        )
        return {row['feed_id']: row['latest_sent'] for row in rows}

    def describe_age(self, sent, now):
        """Describe how long ago an alert was sent, in the coarsest useful unit."""
        seconds = (now - sent).total_seconds()
        if seconds < 0:
            return 'in the future'
        for unit_seconds, unit in ((86400, 'd'), (3600, 'h'), (60, 'm')):
            if seconds >= unit_seconds:
                return f'{int(seconds // unit_seconds)}{unit} ago'
        return f'{int(seconds)}s ago'

    def describe_active_alerts(self, entry_count, latest_sent, now):
        """One line pairing what the feed advertises now with the newest alert stored."""
        parts = []
        if entry_count is not None:
            parts.append(f'{entry_count} alert entr{"y" if entry_count == 1 else "ies"} found.')
        if latest_sent is not None:
            parts.append(f'latest alert sent {latest_sent.isoformat()} ({self.describe_age(latest_sent, now)})')
        else:
            parts.append('no unexpired alert stored.')
        return f'Active alerts: {" ".join(parts)}'

    def describe_historical_alerts(self, feed):
        """Return (has_alerts, message) for anything this feed has ever ingested."""
        if feed.has_alerts:
            return True, 'Historical alerts: ✅ alerts stored for this feed.'
        if feed.has_processed_alerts:
            return False, (
                'Historical alerts: ⚠️ no Alert rows, but alerts have been processed (parsed then discarded/not saved).'
            )
        return False, 'Historical alerts: ❌ no Alert rows and nothing processed — this feed has never been ingested.'

    async def check_feed(self, client, feed, deep):
        """Return (verdict, list_of_message_lines, fetch_seconds, entry_count)."""
        headers = dict(COMMON_REQUESTS_HEADERS)
        if feed.format == Feed.Format.NWS_US:
            # NWS serves GeoJSON by default; the atom variant must be requested explicitly
            # (mirrors apps/cap_feed/formats/nws_us.py).
            headers['Accept'] = 'application/atom+xml'

        started = time.monotonic()
        try:
            response = await client.get(feed.url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as e:
            elapsed = time.monotonic() - started
            return Verdict.UNREACHABLE, [f'Failed to fetch feed after {format_seconds(elapsed)}: {e!r}'], elapsed, None
        elapsed = time.monotonic() - started

        verdict, messages, entry_count = await self.analyse_response(client, feed, response, deep)
        messages.insert(
            0,
            f'HTTP {response.status_code} in {format_seconds(elapsed)}, {len(response.content) / 1024:.1f} KiB.',
        )
        return verdict, messages, elapsed, entry_count

    async def analyse_response(self, client, feed, response, deep):
        """Return (verdict, list_of_message_lines, entry_count) for an already-fetched feed index.

        entry_count is None when the index could not be parsed far enough to count entries.
        """
        messages = []

        if not response.content or response.content.strip() == b'':
            return Verdict.EMPTY, ['Feed returned empty content.'], None

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            return Verdict.INVALID_XML, [f'Response is not well-formed XML: {e}'], None

        structure = detect_structure(root)
        if structure == 'unknown':
            return (
                Verdict.UNKNOWN_STRUCTURE,
                [f'Unrecognised root element <{local_tag(root.tag)}> (expected <rss> or <feed>).'],
                None,
            )

        compatible_formats = STRUCTURE_TO_FORMATS[structure]
        entry_count = count_entries(root, feed.format)

        if feed.format not in compatible_formats:
            suggested = sorted(f.value for f in compatible_formats)
            messages.append(
                f'Configured format is "{feed.format}" but served structure is <{structure}> '
                f'(root <{local_tag(root.tag)}>). Suggested format: {" or ".join(suggested)}.'
            )
            return Verdict.MISMATCH, messages, entry_count

        if feed.format == Feed.Format.ATOM and requires_cap_link(root):
            messages.append(
                f'Configured format is "{feed.format}" but <atom:id> is not a url, so no CAP document can be '
                f'fetched and every entry is skipped. Suggested format: {Feed.Format.NWS_US.value}.'
            )
            return Verdict.MISMATCH, messages, entry_count

        # Structure matches the configured format; make sure the parser can actually see entries.
        if entry_count == 0:
            messages.append(
                f'Structure matches format "{feed.format}" but 0 alert entries were found. '
                'Feed may be genuinely empty, or its inner structure changed.'
            )
            return Verdict.EMPTY, messages, entry_count

        if deep:
            messages.extend(await self.deep_check(client, root, feed))

        return Verdict.OK, messages, entry_count

    async def deep_check(self, client, root, feed):
        link = first_alert_link(root, feed.format)
        if not link:
            return ['[deep] Could not extract first alert link.']
        started = time.monotonic()
        try:
            resp = await client.get(link, headers=COMMON_REQUESTS_HEADERS)
            resp.raise_for_status()
            alert_root = ET.fromstring(resp.content)
        except httpx.HTTPError as e:
            took = format_seconds(time.monotonic() - started)
            return [f'[deep] Failed to fetch first alert doc after {took} ({link}): {e!r}']
        except ET.ParseError as e:
            return [f'[deep] First alert doc is not well-formed XML ({link}): {e}']
        took = format_seconds(time.monotonic() - started)

        if local_tag(alert_root.tag) == 'alert' and CAP_NS_PREFIX in alert_root.tag:
            return [f'[deep] First alert doc is valid CAP, fetched in {took}: {link}']
        return [f'[deep] First alert doc is NOT a CAP <alert> (root <{alert_root.tag}>), fetched in {took}: {link}']

    async def run_checks(self, feeds, options, on_progress):
        """Fetch and check all feeds concurrently. Results are returned in feed order."""
        concurrency = max(1, options['concurrency'])
        semaphore = asyncio.Semaphore(concurrency)

        async with httpx.AsyncClient(
            timeout=options['timeout'],
            follow_redirects=True,
            limits=httpx.Limits(max_connections=concurrency),
        ) as client:

            async def run_one(feed):
                async with semaphore:
                    try:
                        verdict, messages, elapsed, entry_count = await self.check_feed(client, feed, options['deep'])
                    except Exception as e:
                        # A single misbehaving feed must not abort the whole run.
                        verdict = Verdict.UNREACHABLE
                        messages = [f'Unexpected error while checking feed: {e!r}']
                        elapsed = None
                        entry_count = None
                on_progress(feed, verdict, elapsed)
                return verdict, messages, elapsed, entry_count

            return await asyncio.gather(*(run_one(feed) for feed in feeds))

    def render_progress(self, done, total, counts, feed, elapsed):
        breakdown = ', '.join(f'{verdict}={count}' for verdict, count in sorted(counts.items()))
        iso3 = feed.country.iso3 if feed.country_id else '???'
        took = format_seconds(elapsed) if elapsed is not None else 'n/a'
        line = f'  [{done}/{total}] {breakdown} | last: feed #{feed.pk} ({iso3}) {took}'
        self.stdout.write(f'\r{line[:PROGRESS_WIDTH]:<{PROGRESS_WIDTH}}', ending='')
        self.stdout.flush()

    def handle(self, *_, **options):
        # Materialised up front: the async fetch phase cannot touch the ORM.
        feeds = list(self.get_queryset(options))
        total = len(feeds)
        if total == 0:
            self.stdout.write(self.style.WARNING('No feeds matched the given filters.'))
            return

        self.stdout.write(f'Checking {total} feed(s), {max(1, options["concurrency"])} at a time...')

        # The in-place progress line needs a terminal; piped output gets the report only.
        show_progress = options['verbosity'] > 0 and getattr(self.stdout, 'isatty', lambda: False)()
        fetch_counts = {}

        def on_progress(feed, verdict, elapsed):
            fetch_counts[verdict] = fetch_counts.get(verdict, 0) + 1
            if show_progress:
                self.render_progress(sum(fetch_counts.values()), total, fetch_counts, feed, elapsed)

        results = asyncio.run(self.run_checks(feeds, options, on_progress))

        if show_progress:
            # Drop the progress line before writing the per-feed report.
            self.stdout.write(f'\r{"":<{PROGRESS_WIDTH}}\r', ending='')

        now = timezone.now()
        latest_sent = {}
        if not options['skip_db']:
            started = time.monotonic()
            latest_sent = self.get_latest_sent(feeds)
            self.stdout.write(f'Latest-alert lookup took {format_seconds(time.monotonic() - started)}.')

        style_for = {
            Verdict.OK: self.style.SUCCESS,
            Verdict.MISMATCH: self.style.ERROR,
            Verdict.UNREACHABLE: self.style.ERROR,
            Verdict.INVALID_XML: self.style.ERROR,
            Verdict.UNKNOWN_STRUCTURE: self.style.ERROR,
            Verdict.EMPTY: self.style.WARNING,
            Verdict.NOT_INGESTED: self.style.WARNING,
        }

        counts = {}
        problems = 0
        timings = []
        for feed, (verdict, messages, elapsed, entry_count) in zip(feeds, results):
            if elapsed is not None:
                timings.append((elapsed, feed))

            if not options['skip_db']:
                messages.append(self.describe_active_alerts(entry_count, latest_sent.get(feed.pk), now))
                has_alerts, historical_message = self.describe_historical_alerts(feed)
                messages.append(historical_message)
                if verdict == Verdict.OK and not has_alerts:
                    verdict = Verdict.NOT_INGESTED
            elif entry_count is not None:
                messages.append(f'{entry_count} alert entr{"y" if entry_count == 1 else "ies"} found.')

            counts[verdict] = counts.get(verdict, 0) + 1
            if verdict != Verdict.OK:
                problems += 1
            elif options['only_issues']:
                continue

            style = style_for.get(verdict, self.style.NOTICE)
            iso3 = feed.country.iso3 if feed.country_id else '???'
            took = format_seconds(elapsed) if elapsed is not None else 'n/a'
            self.stdout.write(style(f'[{verdict}] feed #{feed.pk} ({iso3}, format={feed.format}, {took}) {feed.url}'))
            for msg in messages:
                self.stdout.write(f'    {msg}')

        self.stdout.write('\nSummary:')
        for verdict, count in sorted(counts.items()):
            self.stdout.write(f'    {verdict}: {count}')

        if timings:
            durations = sorted(elapsed for elapsed, _ in timings)
            slowest = sorted(timings, key=lambda item: item[0], reverse=True)[:SLOWEST_COUNT]
            self.stdout.write('\nResponse times:')
            self.stdout.write(
                f'    min {format_seconds(durations[0])}, '
                f'median {format_seconds(durations[len(durations) // 2])}, '
                f'max {format_seconds(durations[-1])}'
            )
            self.stdout.write(f'    slowest {len(slowest)}:')
            for elapsed, feed in slowest:
                iso3 = feed.country.iso3 if feed.country_id else '???'
                self.stdout.write(f'        {format_seconds(elapsed):>8}  feed #{feed.pk} ({iso3}) {feed.url}')

        if problems and options['strict']:
            raise CommandError(f'{problems} feed(s) reported problems.')
