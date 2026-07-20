import xml.etree.ElementTree as ET

import httpx
from django.core.management.base import BaseCommand, CommandError

from apps.cap_feed.formats.utils import COMMON_REQUESTS_HEADERS
from apps.cap_feed.models import Feed

# Namespaces used to navigate the feed index documents.
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'cap': 'urn:oasis:names:tc:emergency:cap:1.2',
}

# CAP namespace prefix (version agnostic) used to validate individual alert docs.
CAP_NS_PREFIX = 'urn:oasis:names:tc:emergency:cap'

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
        # NWS points to the CAP doc via <link href="...">.
        link = entry.find('atom:link', NS)
        return link.attrib.get('href') if link is not None else None
    # Plain atom: the <id> is the CAP doc URL.
    id_el = entry.find('atom:id', NS)
    return id_el.text if id_el is not None else None


class Command(BaseCommand):
    help = (
        'Check that each feed\'s configured `format` matches the structure actually served, '
        'plus reachability / well-formedness / non-empty checks. Read-only; does not modify feeds.'
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
            '--strict',
            action='store_true',
            help='Exit with an error if any feed has a problem (useful for CI).',
        )

    def get_queryset(self, options):
        qs = Feed.objects.select_related('country').all()
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

    def check_feed(self, feed, timeout, deep):
        """Return (verdict, list_of_message_lines)."""
        messages = []

        headers = dict(COMMON_REQUESTS_HEADERS)
        if feed.format == Feed.Format.NWS_US:
            # NWS serves GeoJSON by default; the atom variant must be requested explicitly
            # (mirrors apps/cap_feed/formats/nws_us.py).
            headers['Accept'] = 'application/atom+xml'

        try:
            response = httpx.get(feed.url, headers=headers, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            return Verdict.UNREACHABLE, [f'Failed to fetch feed: {e!r}']

        if not response.content or response.content.strip() == b'':
            return Verdict.EMPTY, ['Feed returned empty content.']

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            return Verdict.INVALID_XML, [f'Response is not well-formed XML: {e}']

        structure = detect_structure(root)
        if structure == 'unknown':
            return Verdict.UNKNOWN_STRUCTURE, [
                f'Unrecognised root element <{local_tag(root.tag)}> (expected <rss> or <feed>).'
            ]

        compatible_formats = STRUCTURE_TO_FORMATS[structure]
        entry_count = count_entries(root, feed.format)

        if feed.format not in compatible_formats:
            suggested = sorted(f.value for f in compatible_formats)
            messages.append(
                f'Configured format is "{feed.format}" but served structure is <{structure}> '
                f'(root <{local_tag(root.tag)}>). Suggested format: {" or ".join(suggested)}.'
            )
            return Verdict.MISMATCH, messages

        # Structure matches the configured format; make sure the parser can actually see entries.
        if entry_count == 0:
            messages.append(
                f'Structure matches format "{feed.format}" but 0 alert entries were found. '
                'Feed may be genuinely empty, or its inner structure changed.'
            )
            return Verdict.EMPTY, messages

        messages.append(f'{entry_count} alert entr{"y" if entry_count == 1 else "ies"} found.')

        if deep:
            messages.extend(self.deep_check(root, feed, timeout))

        return Verdict.OK, messages

    def deep_check(self, root, feed, timeout):
        link = first_alert_link(root, feed.format)
        if not link:
            return ['[deep] Could not extract first alert link.']
        try:
            resp = httpx.get(link, headers=COMMON_REQUESTS_HEADERS, timeout=timeout)
            resp.raise_for_status()
            alert_root = ET.fromstring(resp.content)
        except httpx.HTTPError as e:
            return [f'[deep] Failed to fetch first alert doc ({link}): {e!r}']
        except ET.ParseError as e:
            return [f'[deep] First alert doc is not well-formed XML ({link}): {e}']

        if local_tag(alert_root.tag) == 'alert' and CAP_NS_PREFIX in alert_root.tag:
            return [f'[deep] First alert doc is valid CAP: {link}']
        return [f'[deep] First alert doc is NOT a CAP <alert> (root <{alert_root.tag}>): {link}']

    def handle(self, *_, **options):
        feeds = self.get_queryset(options)
        total = feeds.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No feeds matched the given filters.'))
            return

        self.stdout.write(f'Checking {total} feed(s)...\n')

        style_for = {
            Verdict.OK: self.style.SUCCESS,
            Verdict.MISMATCH: self.style.ERROR,
            Verdict.UNREACHABLE: self.style.ERROR,
            Verdict.INVALID_XML: self.style.ERROR,
            Verdict.UNKNOWN_STRUCTURE: self.style.ERROR,
            Verdict.EMPTY: self.style.WARNING,
        }

        counts = {}
        problems = 0
        for feed in feeds:
            verdict, messages = self.check_feed(feed, options['timeout'], options['deep'])
            counts[verdict] = counts.get(verdict, 0) + 1
            if verdict != Verdict.OK:
                problems += 1

            style = style_for.get(verdict, self.style.NOTICE)
            iso3 = feed.country.iso3 if feed.country_id else '???'
            self.stdout.write(style(f'[{verdict}] feed #{feed.pk} ({iso3}, format={feed.format}) {feed.url}'))
            for msg in messages:
                self.stdout.write(f'    {msg}')

        self.stdout.write('\nSummary:')
        for verdict, count in sorted(counts.items()):
            self.stdout.write(f'    {verdict}: {count}')

        if problems and options['strict']:
            raise CommandError(f'{problems} feed(s) reported problems.')
