import asyncio
import datetime
import email.utils
import re
import time
import xml.etree.ElementTree as ET
from typing import NamedTuple

import httpx
import validators
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Exists, Max, OuterRef
from django.utils import timezone

from apps.cap_feed.formats.utils import COMMON_REQUESTS_HEADERS, find_cap_link
from apps.cap_feed.models import Alert, Feed, FeedLog, ProcessedAlert

# Namespaces used to navigate the feed index documents.
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'cap': 'urn:oasis:names:tc:emergency:cap:1.2',
}

# CAP namespace prefix (version agnostic) used to validate individual alert docs.
CAP_NS_PREFIX = 'urn:oasis:names:tc:emergency:cap'

# Width of the single-line progress indicator; wide enough for the verdict breakdown.
PROGRESS_WIDTH = 110

# Width of the `─── VERDICT (n) ───` rules that separate the report sections.
SECTION_WIDTH = 60

# How many slowest feeds the response-time summary lists.
SLOWEST_COUNT = 5

# How much of an unusable response body is echoed as evidence.
SNIPPET_LENGTH = 160

# How much of a feed log's error message is echoed.
LOG_MESSAGE_LENGTH = 140

# FeedLog.save() prunes rows older than this, so log counts are always over this window.
LOG_RETENTION = '14d'

# Root structure -> feed formats that are able to parse it.
STRUCTURE_TO_FORMATS = {
    'rss': {Feed.Format.RSS},
    'atom': {Feed.Format.ATOM, Feed.Format.NWS_US},
}

# Entry tag each structure holds its alerts in, used to report entries found under the
# structure the feed does *not* serve.
STRUCTURE_ENTRY_PATHS = {
    'rss': ('<item>', './/item'),
    'atom': ('<atom:entry>', f'.//{{{NS["atom"]}}}entry'),
}


class Verdict:
    OK = 'OK'
    MISMATCH = 'MISMATCH'
    EMPTY = 'EMPTY'
    UNREACHABLE = 'UNREACHABLE'
    INVALID_XML = 'INVALID_XML'
    UNKNOWN_STRUCTURE = 'UNKNOWN_STRUCTURE'
    NOT_INGESTED = 'NOT_INGESTED'


# Verdicts worst-first: the order report sections and the summary line are laid out in,
# so the feeds needing attention are read before the ones that are fine.
VERDICT_ORDER = (
    Verdict.UNREACHABLE,
    Verdict.INVALID_XML,
    Verdict.UNKNOWN_STRUCTURE,
    Verdict.MISMATCH,
    Verdict.EMPTY,
    Verdict.NOT_INGESTED,
    Verdict.OK,
)


def verdict_rank(verdict: str) -> int:
    """Sort key placing the worst verdicts first; unlisted verdicts sort last."""
    try:
        return VERDICT_ORDER.index(verdict)
    except ValueError:
        return len(VERDICT_ORDER)


class IndexMeta(NamedTuple):
    """What the feed index says about itself, independent of the alerts it lists."""

    title: str | None
    updated: datetime.datetime | None
    newest_entry: datetime.datetime | None


class CheckResult(NamedTuple):
    """Outcome of the network phase for one feed.

    `details` are ordered (label, text) pairs; the report renders them as aligned lines
    under the feed's header, so each label owns one facet of what was observed.
    """

    verdict: str
    details: list[tuple[str, str]]
    elapsed: float | None
    entry_count: int | None
    index_meta: IndexMeta


class FeedReport(NamedTuple):
    """A checked feed plus the database context the report needs, ready to render."""

    feed: Feed
    verdict: str
    details: list[tuple[str, str]]
    elapsed: float | None
    entry_count: int | None
    index_meta: IndexMeta
    latest_sent: datetime.datetime | None


EMPTY_INDEX_META = IndexMeta(title=None, updated=None, newest_entry=None)


def format_seconds(seconds: float) -> str:
    """Format a duration for the report, keeping sub-second timings readable."""
    if seconds < 1:
        return f'{seconds * 1000:.0f}ms'
    return f'{seconds:.2f}s'


def format_datetime(value: datetime.datetime) -> str:
    """Format a timestamp as a compact UTC instant."""
    return value.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def format_age(value: datetime.datetime, now: datetime.datetime) -> str:
    """Describe how long ago something happened, in the coarsest useful unit."""
    seconds = (now - value).total_seconds()
    if seconds < 0:
        return 'in the future'
    for unit_seconds, unit in ((86400, 'd'), (3600, 'h'), (60, 'm')):
        if seconds >= unit_seconds:
            return f'{int(seconds // unit_seconds)}{unit} ago'
    return f'{int(seconds)}s ago'


def local_tag(tag: str) -> str:
    """Return the namespace-stripped, lower-cased local name of an XML tag."""
    if '}' in tag:
        tag = tag.split('}', 1)[1]
    return tag.lower()


def element_text(parent: ET.Element | None, path: str, ns: dict[str, str] | None = None) -> str | None:
    """Return the collapsed text of the first matching child, or None."""
    if parent is None:
        return None
    element = parent.find(path, ns) if ns else parent.find(path)
    if element is None or not element.text:
        return None
    return re.sub(r'\s+', ' ', element.text).strip() or None


def parse_index_datetime(raw: str | None) -> datetime.datetime | None:
    """Parse a feed timestamp, accepting both the atom (ISO) and rss (RFC 822) spellings."""
    if not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        pass
    try:
        return email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None


def plural(count: int, noun: str, plural_noun: str | None = None) -> str:
    """Render a count with its noun agreeing in number."""
    return f'{count} {noun if count == 1 else (plural_noun or noun + "s")}'


def truncate(text: str, limit: int) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    return text if len(text) <= limit else f'{text[:limit]}…'


def content_snippet(content: bytes) -> str:
    """A one-line, printable head of a response body, for evidence on unusable responses."""
    decoded = content[: SNIPPET_LENGTH * 4].decode('utf-8', errors='replace')
    return truncate(decoded, SNIPPET_LENGTH)


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


def read_index_meta(root: ET.Element, structure: str) -> IndexMeta:
    """Read the index's self-description: its title, when it changed, and its newest entry."""
    if structure == 'rss':
        channel = root.find('channel')
        title = element_text(channel, 'title')
        updated = parse_index_datetime(
            element_text(channel, 'lastBuildDate') or element_text(channel, 'pubDate'),
        )
        entry_dates = [parse_index_datetime(element_text(item, 'pubDate')) for item in root.findall('.//item')]
    else:
        title = element_text(root, 'atom:title', NS)
        updated = parse_index_datetime(element_text(root, 'atom:updated', NS))
        entry_dates = [
            parse_index_datetime(element_text(entry, 'atom:updated', NS) or element_text(entry, 'atom:published', NS))
            for entry in root.findall('atom:entry', NS)
        ]
    known = [date for date in entry_dates if date is not None]
    return IndexMeta(title=title, updated=updated, newest_entry=max(known) if known else None)


def describe_child_tags(root: ET.Element) -> str:
    """Summarise the direct children of an element as `tag×count`, in document order."""
    counts: dict[str, int] = {}
    for child in root:
        counts[local_tag(child.tag)] = counts.get(local_tag(child.tag), 0) + 1
    return ' · '.join(f'<{tag}>×{count}' for tag, count in counts.items()) or 'no children'


def count_foreign_entries(root: ET.Element, structure: str) -> tuple[str, int] | None:
    """Count entries belonging to the structure this document is *not* — the usual sign
    of a feed whose inner markup no longer matches its root element."""
    other = 'atom' if structure == 'rss' else 'rss'
    label, path = STRUCTURE_ENTRY_PATHS[other]
    found = len(root.findall(path))
    return (label, found) if found else None


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


def cap_namespace(root: ET.Element) -> dict[str, str]:
    """Build a namespace map for a CAP document, honouring whichever version it declares."""
    if root.tag.startswith('{'):
        return {'cap': root.tag[1:].split('}', 1)[0]}
    return {}


def join_parts(*parts: str | None, separator: str = ' · ') -> str:
    """Join the parts that have a value, dropping the ones that do not apply."""
    return separator.join(part for part in parts if part)


def describe_cap_alert(root: ET.Element, now: datetime.datetime) -> list[str]:
    """Summarise the CAP fields that decide whether an alert is ingestable."""
    ns = cap_namespace(root)
    prefix = 'cap:' if ns else ''

    def field(parent, name):
        return element_text(parent, f'{prefix}{name}', ns or None)

    def children(parent, name):
        return parent.findall(f'{prefix}{name}', ns or None)

    version = ns['cap'].rsplit(':', 1)[-1] if ns else 'no namespace'
    sender, identifier = field(root, 'sender'), field(root, 'identifier')
    sent = parse_index_datetime(field(root, 'sent'))
    lines = [
        join_parts(
            f'CAP {version}',
            f'sender={sender}' if sender else None,
            f'identifier={identifier}' if identifier else None,
        ),
        join_parts(
            f'sent {format_datetime(sent)} ({format_age(sent, now)})' if sent else None,
            join_parts(field(root, 'status'), field(root, 'msgType'), field(root, 'scope'), separator='/') or None,
        ),
    ]

    infos = children(root, 'info')
    if not infos:
        lines.append('no <info> block — nothing to ingest')
        return [line for line in lines if line]

    info = infos[0]
    event, language = field(info, 'event'), field(info, 'language')
    lines.append(
        join_parts(
            plural(len(infos), 'info block'),
            f'event="{truncate(event, 60)}"' if event else None,
            join_parts(field(info, 'severity'), field(info, 'urgency'), field(info, 'certainty'), separator='/') or None,
            f'lang={language}' if language else None,
            plural(len(children(info, 'area')), 'area'),
        )
    )
    return [line for line in lines if line]


class Command(BaseCommand):
    help = (
        'Check that each feed\'s configured `format` matches the structure actually served, '
        'plus reachability / well-formedness / non-empty checks and whether any alerts are '
        'stored in the database. Feeds are fetched in parallel. Read-only; does not modify feeds.'
    )

    # OK feeds are reported as a table: (heading, alignment) per column. STORED reports the
    # newest alert held in the database, so it is dropped when the database is not consulted.
    OK_COLUMNS = (
        ('FEED', '<'),
        ('ISO3', '<'),
        ('FORMAT', '<'),
        ('TIME', '>'),
        ('ENTRIES', '>'),
        ('NEWEST', '>'),
        ('STORED', '>'),
        ('FLAGS', '<'),
    )
    DB_ONLY_COLUMNS = frozenset({'STORED'})

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
            help='Also fetch the first alert document per feed and report its CAP metadata.',
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
            help='Skip the stored-alert and feed-log lookups.',
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

    def get_feed_logs(self, feeds):
        """Map feed id -> (log_count, latest_log) over the retained log window.

        FeedLog rows are the aggregator's own account of why a feed failed to ingest, so
        they explain verdicts the HTTP check alone cannot.
        """
        feed_ids = [feed.pk for feed in feeds]
        counts = {
            row['feed_id']: row['log_count']
            for row in FeedLog.objects.filter(feed__in=feed_ids).values('feed_id').annotate(log_count=Count('pk'))
        }
        latest = {
            row['feed_id']: row
            for row in FeedLog.objects.filter(feed__in=feed_ids)
            .order_by('feed_id', '-timestamp')
            .distinct('feed_id')
            .values('feed_id', 'timestamp', 'exception', 'error_message', 'alert_url')
        }
        return {feed_id: (counts.get(feed_id, 0), latest.get(feed_id)) for feed_id in counts}

    def feed_iso3(self, feed):
        return feed.country.iso3 if feed.country_id else '???'

    def feed_flags(self, feed):
        """The configuration flags worth flagging: everything that is not the healthy default."""
        flags = []
        if feed.status != Feed.Status.ACTIVE:
            flags.append(f'status={feed.status}')
        if not feed.enable_polling:
            flags.append('polling=off')
        if feed.is_archived:
            flags.append('archived')
        if not feed.official:
            flags.append('unofficial')
        return flags

    def describe_feed_config(self, feed):
        """The feed's own record: how it is configured and who to ask about it."""
        parts = [
            f'status={feed.status}',
            f'polling=every {feed.polling_interval}s' if feed.enable_polling else 'polling=off',
            f'rebroadcast={"on" if feed.enable_rebroadcast else "off"}',
            'official' if feed.official else 'unofficial',
        ]
        if feed.is_archived:
            archived_at = f' at {format_datetime(feed.archived_at)}' if feed.archived_at else ''
            parts.append(f'archived{archived_at}')
        author = ' '.join(part for part in (feed.author_name, f'<{feed.author_email}>' if feed.author_email else '') if part)
        if author:
            parts.append(f'author={author}')
        return ' · '.join(parts)

    def describe_http(self, response, elapsed):
        """Status, size, media type, and where the request actually ended up."""
        parts = [
            f'{response.status_code} {response.reason_phrase}'.strip(),
            format_seconds(elapsed),
            f'{len(response.content) / 1024:.1f} KiB',
            response.headers.get('content-type', 'no content-type'),
        ]
        for header in ('last-modified', 'etag'):
            if response.headers.get(header):
                parts.append(f'{header}={truncate(response.headers[header], 40)}')
        if response.history:
            parts.append(f'{plural(len(response.history), "redirect")} → {response.url}')
        return ' · '.join(parts)

    def describe_index(self, structure, meta, entry_count, now):
        """What the index says about itself, next to what the parser found in it."""
        parts = [f'<{structure}>']
        if meta.title:
            parts.append(f'title="{truncate(meta.title, 60)}"')
        if meta.updated:
            parts.append(f'updated {format_datetime(meta.updated)} ({format_age(meta.updated, now)})')
        parts.append(self.describe_entries(entry_count))
        if meta.newest_entry:
            parts.append(f'newest entry {format_datetime(meta.newest_entry)} ({format_age(meta.newest_entry, now)})')
        return ' · '.join(parts)

    def describe_entries(self, entry_count):
        """Describe how many alert entries the configured parser found in the index."""
        if entry_count is None:
            return 'entries n/a'
        return plural(entry_count, 'entry', 'entries')

    def describe_stored_alerts(self, feed, entry_count, latest_sent, now):
        """What the database holds for this feed, live alerts first then its whole history."""
        if latest_sent is None:
            live = 'no unexpired alert stored'
        else:
            live = f'latest unexpired alert sent {format_datetime(latest_sent)} ({format_age(latest_sent, now)})'
        if feed.has_alerts:
            history = 'Alert rows exist'
        elif feed.has_processed_alerts:
            history = 'no Alert rows, but alerts have been processed (parsed then discarded)'
        else:
            history = 'never ingested — no Alert rows, nothing processed'
        # An index that could not be parsed advertises nothing worth reporting here.
        advertised = f'{plural(entry_count, "entry", "entries")} advertised' if entry_count is not None else None
        return join_parts(advertised, live, history)

    def describe_feed_log(self, log_count, latest_log, now):
        """The most recent thing the aggregator recorded against this feed."""
        if not log_count or latest_log is None:
            return None
        timestamp = latest_log['timestamp']
        parts = [
            f'{plural(log_count, "log")} in last {LOG_RETENTION}',
            f'latest {format_datetime(timestamp)} ({format_age(timestamp, now)})',
            latest_log['exception'],
        ]
        if latest_log['error_message']:
            parts.append(truncate(latest_log['error_message'], LOG_MESSAGE_LENGTH))
        if latest_log['alert_url']:
            parts.append(latest_log['alert_url'])
        return ' · '.join(parts)

    def describe_hint(self, feed, verdict):
        """A next step, only where the metadata makes one unambiguous."""
        if verdict == Verdict.NOT_INGESTED and not feed.enable_polling:
            return 'polling is disabled for this feed, so it will never ingest until enable_polling is set.'
        if verdict == Verdict.NOT_INGESTED and feed.has_processed_alerts:
            return 'alerts reach the parser but no Alert row survives — check the feed logs above and the CAP contents.'
        if verdict == Verdict.NOT_INGESTED:
            return 'the index parses but nothing has ever been ingested — run the poll for this feed and watch its logs.'
        return None

    async def check_feed(self, client, feed, deep, now) -> CheckResult:
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
            return CheckResult(
                verdict=Verdict.UNREACHABLE,
                details=self.describe_fetch_failure(e, elapsed),
                elapsed=elapsed,
                entry_count=None,
                index_meta=EMPTY_INDEX_META,
            )
        elapsed = time.monotonic() - started

        result = await self.analyse_response(client, feed, response, deep, now)
        return result._replace(
            details=[('http', self.describe_http(response, elapsed)), *result.details],
            elapsed=elapsed,
        )

    def describe_fetch_failure(self, error, elapsed):
        """Report a failed fetch by what actually went wrong, with the server's own words."""
        details = []
        response = getattr(error, 'response', None)
        if response is not None:
            details.append(
                (
                    'http',
                    f'{response.status_code} {response.reason_phrase} · {format_seconds(elapsed)} · '
                    f'{response.headers.get("content-type", "no content-type")} · {response.url}',
                )
            )
        details.append(('issue', f'{type(error).__name__} after {format_seconds(elapsed)}: {error}'))
        if response is not None and response.content:
            details.append(('body', content_snippet(response.content)))
        return details

    async def analyse_response(self, client, feed, response, deep, now) -> CheckResult:
        """Judge an already-fetched feed index.

        The returned `elapsed` is left unset; the caller owns the fetch timing. `entry_count`
        is None when the index could not be parsed far enough to count entries.
        """

        def result(verdict, details, entry_count=None, index_meta=EMPTY_INDEX_META):
            return CheckResult(verdict, list(details), None, entry_count, index_meta)

        if not response.content or response.content.strip() == b'':
            return result(Verdict.EMPTY, [('issue', 'feed returned an empty body.')])

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            return result(
                Verdict.INVALID_XML,
                [
                    ('issue', f'response is not well-formed XML: {e}'),
                    ('body', content_snippet(response.content)),
                ],
            )

        structure = detect_structure(root)
        if structure == 'unknown':
            return result(
                Verdict.UNKNOWN_STRUCTURE,
                [
                    ('issue', f'unrecognised root element <{local_tag(root.tag)}>, expected <rss> or <feed>.'),
                    ('markup', f'root children: {describe_child_tags(root)}'),
                    ('body', content_snippet(response.content)),
                ],
            )

        entry_count = count_entries(root, feed.format)
        meta = read_index_meta(root, structure)
        details = [('index', self.describe_index(structure, meta, entry_count, now))]
        compatible_formats = STRUCTURE_TO_FORMATS[structure]

        if feed.format not in compatible_formats:
            suggested = ' or '.join(sorted(f.value for f in compatible_formats))
            details.append(
                (
                    'issue',
                    f'configured format "{feed.format}" cannot read a <{structure}> index '
                    f'(root <{local_tag(root.tag)}>) — suggested format: {suggested}.',
                )
            )
            return result(Verdict.MISMATCH, details, entry_count, meta)

        if feed.format == Feed.Format.ATOM and requires_cap_link(root):
            first_id = element_text(root.find('atom:entry', NS), 'atom:id', NS)
            details.append(
                (
                    'issue',
                    f'configured format "{feed.format}" reads the CAP document from <atom:id>, but that is not a url '
                    f'({first_id or "missing"}), so every entry is skipped — '
                    f'suggested format: {Feed.Format.NWS_US.value}.',
                )
            )
            return result(Verdict.MISMATCH, details, entry_count, meta)

        # Structure matches the configured format; make sure the parser can actually see entries.
        if entry_count == 0:
            details.append(
                (
                    'issue',
                    f'structure matches format "{feed.format}" but no alert entries were found — '
                    'the feed may be genuinely empty, or its inner markup changed.',
                )
            )
            details.append(('markup', f'root children: {describe_child_tags(root)}'))
            foreign = count_foreign_entries(root, structure)
            if foreign:
                label, found = foreign
                details.append(
                    ('markup', f'{plural(found, f"{label} element")} present, which a <{structure}> index does not use.')
                )
            return result(Verdict.EMPTY, details, entry_count, meta)

        if deep:
            details.extend(await self.deep_check(client, root, feed, now))

        return result(Verdict.OK, details, entry_count, meta)

    async def deep_check(self, client, root, feed, now):
        """Fetch the first alert document and report the CAP metadata the ingest depends on."""
        link = first_alert_link(root, feed.format)
        if not link:
            return [('deep', 'could not extract the first alert link from the index.')]
        started = time.monotonic()
        try:
            response = await client.get(link, headers=COMMON_REQUESTS_HEADERS)
            response.raise_for_status()
            alert_root = ET.fromstring(response.content)
        except httpx.HTTPError as e:
            took = format_seconds(time.monotonic() - started)
            return [('deep', f'failed to fetch the first alert doc after {took}: {type(e).__name__}: {e}'), ('deep', link)]
        except ET.ParseError as e:
            return [('deep', f'first alert doc is not well-formed XML: {e}'), ('deep', link)]
        took = format_seconds(time.monotonic() - started)

        if local_tag(alert_root.tag) != 'alert' or CAP_NS_PREFIX not in alert_root.tag:
            return [
                ('deep', f'first alert doc is not a CAP <alert> (root <{alert_root.tag}>), fetched in {took}.'),
                ('deep', link),
            ]
        lines = [f'first alert doc fetched in {took}, {len(response.content) / 1024:.1f} KiB']
        lines.extend(describe_cap_alert(alert_root, now))
        lines.append(link)
        return [('deep', line) for line in lines]

    async def run_checks(self, feeds, options, now, on_progress):
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
                        result = await self.check_feed(client, feed, options['deep'], now)
                    except Exception as e:
                        # A single misbehaving feed must not abort the whole run.
                        result = CheckResult(
                            verdict=Verdict.UNREACHABLE,
                            details=[('issue', f'unexpected error while checking feed: {type(e).__name__}: {e}')],
                            elapsed=None,
                            entry_count=None,
                            index_meta=EMPTY_INDEX_META,
                        )
                on_progress(feed, result.verdict, result.elapsed)
                return result

            return await asyncio.gather(*(run_one(feed) for feed in feeds))

    def render_progress(self, done, total, counts, feed, elapsed):
        breakdown = ' · '.join(
            f'{count} {verdict}' for verdict, count in sorted(counts.items(), key=lambda item: verdict_rank(item[0]))
        )
        took = format_seconds(elapsed) if elapsed is not None else 'n/a'
        line = f'  [{done}/{total}] {breakdown} | last: feed #{feed.pk} ({self.feed_iso3(feed)}) {took}'
        self.stdout.write(f'\r{line[:PROGRESS_WIDTH]:<{PROGRESS_WIDTH}}', ending='')
        self.stdout.flush()

    def section_rule(self, verdict, count):
        """A `─── VERDICT (n) ───` rule introducing one verdict's feeds."""
        label = f'─── {verdict} ({count}) '
        return label + '─' * max(3, SECTION_WIDTH - len(label))

    def render_problem_block(self, report, style):
        """Header line plus every labelled detail gathered for a feed that needs attention."""
        took = format_seconds(report.elapsed) if report.elapsed is not None else 'n/a'
        self.stdout.write(
            style(
                f'[{report.verdict}] feed #{report.feed.pk} ({self.feed_iso3(report.feed)}, '
                f'format={report.feed.format}, {took}) {report.feed.url}'
            )
        )
        label_width = max(len(label) for label, _ in report.details)
        for label, value in report.details:
            self.stdout.write(f'    {label:<{label_width}}  {value}')

    def ok_row(self, report, now):
        """The table cells describing one healthy feed, keyed by column heading."""
        return {
            'FEED': f'#{report.feed.pk}',
            'ISO3': self.feed_iso3(report.feed),
            'FORMAT': report.feed.format,
            'TIME': format_seconds(report.elapsed) if report.elapsed is not None else 'n/a',
            'ENTRIES': '—' if report.entry_count is None else str(report.entry_count),
            'NEWEST': format_age(report.index_meta.newest_entry, now) if report.index_meta.newest_entry else '—',
            'STORED': format_age(report.latest_sent, now) if report.latest_sent else '—',
            'FLAGS': ' '.join(self.feed_flags(report.feed)),
        }

    def render_ok_rows(self, reports, now, skip_db):
        """A table of healthy feeds, so a long tail of OK feeds stays scannable."""
        columns = [
            (heading, alignment)
            for heading, alignment in self.OK_COLUMNS
            if not (skip_db and heading in self.DB_ONLY_COLUMNS)
        ]
        headings = tuple(heading for heading, _ in columns)
        alignments = tuple(alignment for _, alignment in columns)
        rows = [tuple(self.ok_row(report, now)[heading] for heading in headings) for report in reports]
        widths = [max(len(cell) for cell in column) for column in zip(headings, *rows)]

        def render(cells):
            line = '  ' + '  '.join(
                f'{cell:{alignment}{width}}' for cell, alignment, width in zip(cells, alignments, widths)
            )
            self.stdout.write(line.rstrip())

        render(headings)
        for report, cells in zip(reports, rows):
            render(cells)
            for label, value in report.details:
                if label == 'deep':
                    self.stdout.write(f'      {value}')

    def render_timings(self, timings):
        durations = sorted(elapsed for elapsed, _ in timings)
        slowest = sorted(timings, key=lambda item: item[0], reverse=True)[:SLOWEST_COUNT]
        self.stdout.write('\nResponse times:')
        self.stdout.write(
            f'    min {format_seconds(durations[0])} · '
            f'median {format_seconds(durations[len(durations) // 2])} · '
            f'max {format_seconds(durations[-1])}'
        )
        self.stdout.write(f'    slowest {len(slowest)}:')
        for elapsed, feed in slowest:
            self.stdout.write(f'        {format_seconds(elapsed):>8}  feed #{feed.pk} ({self.feed_iso3(feed)}) {feed.url}')

    def build_reports(self, feeds, results, latest_sent, feed_logs, now, skip_db):
        """Pair each check result with its database context and settle the final verdict.

        Detail lines are only assembled for feeds that will be reported as a block; healthy
        feeds carry their metadata in the table row instead.
        """
        reports = []
        for feed, result in zip(feeds, results):
            verdict = result.verdict
            if not skip_db and verdict == Verdict.OK and not feed.has_alerts:
                verdict = Verdict.NOT_INGESTED

            details = list(result.details)
            if verdict != Verdict.OK:
                details.insert(0, ('feed', self.describe_feed_config(feed)))
                if not skip_db:
                    details.append(
                        ('alerts', self.describe_stored_alerts(feed, result.entry_count, latest_sent.get(feed.pk), now))
                    )
                    log_count, latest_log = feed_logs.get(feed.pk, (0, None))
                    log_message = self.describe_feed_log(log_count, latest_log, now)
                    if log_message:
                        details.append(('log', log_message))
                hint = self.describe_hint(feed, verdict)
                if hint:
                    details.append(('hint', hint))

            reports.append(
                FeedReport(
                    feed=feed,
                    verdict=verdict,
                    details=details,
                    elapsed=result.elapsed,
                    entry_count=result.entry_count,
                    index_meta=result.index_meta,
                    latest_sent=latest_sent.get(feed.pk),
                )
            )
        return reports

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

        now = timezone.now()
        results = asyncio.run(self.run_checks(feeds, options, now, on_progress))

        if show_progress:
            # Drop the progress line before writing the per-feed report.
            self.stdout.write(f'\r{"":<{PROGRESS_WIDTH}}\r', ending='')

        latest_sent = {}
        feed_logs = {}
        if not options['skip_db']:
            started = time.monotonic()
            latest_sent = self.get_latest_sent(feeds)
            feed_logs = self.get_feed_logs(feeds)
            self.stdout.write(f'Stored-alert and feed-log lookups took {format_seconds(time.monotonic() - started)}.')

        style_for = {
            Verdict.OK: self.style.SUCCESS,
            Verdict.MISMATCH: self.style.ERROR,
            Verdict.UNREACHABLE: self.style.ERROR,
            Verdict.INVALID_XML: self.style.ERROR,
            Verdict.UNKNOWN_STRUCTURE: self.style.ERROR,
            Verdict.EMPTY: self.style.WARNING,
            Verdict.NOT_INGESTED: self.style.WARNING,
        }

        reports = self.build_reports(feeds, results, latest_sent, feed_logs, now, options['skip_db'])

        by_verdict = {}
        for report in reports:
            by_verdict.setdefault(report.verdict, []).append(report)
        ordered_verdicts = sorted(by_verdict, key=verdict_rank)

        for verdict in ordered_verdicts:
            if verdict == Verdict.OK and options['only_issues']:
                continue
            group = by_verdict[verdict]
            style = style_for.get(verdict, self.style.NOTICE)
            self.stdout.write('')
            self.stdout.write(style(self.section_rule(verdict, len(group))))
            if verdict == Verdict.OK:
                self.render_ok_rows(group, now, options['skip_db'])
            else:
                for report in group:
                    self.render_problem_block(report, style)

        breakdown = ' · '.join(
            style_for.get(verdict, self.style.NOTICE)(f'{len(by_verdict[verdict])} {verdict}')
            for verdict in ordered_verdicts
        )
        self.stdout.write(f'\nSummary: {total} feed(s) · {breakdown}')

        timings = [(report.elapsed, report.feed) for report in reports if report.elapsed is not None]
        if timings:
            self.render_timings(timings)

        problems = sum(len(group) for verdict, group in by_verdict.items() if verdict != Verdict.OK)
        if problems and options['strict']:
            raise CommandError(f'{problems} feed(s) reported problems.')
