import logging
import typing
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx
import pytz

from apps.cap_feed.models import FeedLog

logger = logging.getLogger(__name__)


COMMON_REQUESTS_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',  # noqa
}

# Media types feeds use to advertise a CAP alert document on an <atom:link>.
CAP_LINK_TYPES = (
    'application/cap+xml',
    'application/common-alerting-protocol+xml',
)

# Extensions CAP alert documents are served under, used when a feed labels no media type.
CAP_LINK_SUFFIXES = ('.cap', '.xml')


def find_cap_link(alert_entry, ns) -> str | None:
    """Return the href of the <atom:link> that points at the CAP alert document.

    An entry may carry several links, and the CAP document is not always the first
    one: some feeds list an HTML landing page first and attach CAP as an enclosure.
    Prefer an explicit CAP media type, then an enclosure, then a CAP-looking href.
    """
    links = alert_entry.findall('atom:link', ns)

    for cap_link_type in CAP_LINK_TYPES:
        for link in links:
            if link.attrib.get('type') == cap_link_type:
                return link.attrib.get('href')

    for link in links:
        if link.attrib.get('rel') == 'enclosure':
            return link.attrib.get('href')

    for link in links:
        href = link.attrib.get('href')
        if href and href.lower().endswith(CAP_LINK_SUFFIXES):
            return href

    if links:
        return links[0].attrib.get('href')
    return None


# converts CAP1.2 iso format datetime string to datetime object in UTC timezone
def convert_datetime(original_datetime):
    if original_datetime is None:
        return None
    return datetime.fromisoformat(original_datetime).astimezone(pytz.timezone('UTC'))


def fetch_alert_using_url(url) -> tuple[typing.Literal[False], None] | tuple[typing.Literal[True], ET.Element]:
    # navigate alert
    alert_response = httpx.get(url, headers=COMMON_REQUESTS_HEADERS)
    alert_response_content = alert_response.content
    if alert_response.status_code != 200:
        logger.warning(f'Skipping for url {url}: Invalid status_code {alert_response.status_code}')
        return False, None

    if alert_response_content is None or alert_response_content.strip() == b'':
        logger.warning(f'Skipping for url {url}: Due to empty content')
        return False, None

    try:
        parsed_content = ET.fromstring(alert_response_content)
    except ET.ParseError:
        logger.warning(f'Skipping for url {url}: Fail to parse response as XML')
        return False, None

    return True, parsed_content


def log_requestexception(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'RequestException'
    log.error_message = e
    log.description = (
        'It is likely that connection to this feed is unstable or the cap aggregator has been blocked by the feed server.'
    )
    log.response = (
        'Check that the feed is online and stable.\n'
        'If the feed is stable, the cap aggregator may have been blocked after too many requests.'
        ' This is likely temporary but increasing the polling interval may help prevent this in the future.'
    )
    if url:
        log.alert_url = url
    log.save()


def log_attributeerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'AttributeError'
    log.error_message = e
    log.description = (
        'It is likely that the feed structure has changed and the corresponding feed format needs to be updated.'
    )
    log.response = (
        'Check that the corresponding feed format is able to navigate the feed structure and extract the necessary data.'
    )
    if url:
        log.alert_url = url
    log.save()


def log_integrityerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'IntegrityError'
    log.error_message = e
    log.description = 'This is caused by a violation of the Alert schema.'
    log.response = (
        'Check that the xml elements of the alert contains valid data according to CAP-v1.2 schema.\n'
        'For example, the content of a <polygon> tag cannot be empty since the CAP aggregator'
        ' expects valid data inside this optional tag if it is found.'
    )
    log.alert_url = url
    log.save()


def log_valueerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'ValueError'
    log.error_message = e
    log.description = 'This is caused by a violation of the Alert schema.'
    log.response = (
        'Check that the xml elements of the alert contains valid data according to CAP-v1.2 schema.\n'
        'For example, alphabetic timezone designators such as "Z" must not be used.'
        ' The timezone for UTC must be represented as "-00:00".'
    )
    log.alert_url = url
    log.save()
