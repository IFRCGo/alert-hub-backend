import logging
import xml.etree.ElementTree as ET

import httpx
import validators

from apps.cap_feed.formats.cap_xml import get_alert
from apps.cap_feed.models import Alert, Feed, ProcessedAlert
from utils.common import logger_log_extra

from .utils import COMMON_REQUESTS_HEADERS, fetch_alert_using_url, find_cap_link

logger = logging.getLogger(__name__)


# processing for atom feeds whose <id> is not the CAP document url, so the alert is
# fetched from an <atom:link> instead.
# examples: https://api.weather.gov/alerts/active
#           https://publicalert.pagasa.dost.gov.ph/feeds/
#           https://www.alberta.ca/data/aea/rss/feed-full.atom
def get_alerts_nws_us(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = httpx.get(
            feed.url,
            headers={
                **COMMON_REQUESTS_HEADERS,
                'Accept': 'application/atom+xml',
            },
            timeout=Feed.MAX_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.error(
            '[NWS_US] Failed to fetch feed alerts',
            exc_info=True,
            extra=logger_log_extra(
                {
                    'feed': feed.pk,
                }
            ),
        )
        return alert_urls, polled_alerts_count, valid_poll

    root = ET.fromstring(response.content)
    for alert_entry in root.findall('atom:entry', ns):
        url = None
        try:
            url_element = alert_entry.find('atom:id', ns)
            if url_element is None:
                raise Exception('atom:id not found')
            url = url_element.text
            if url is None:
                raise Exception('URL is None')

            cap_link = find_cap_link(alert_entry, ns)
            if cap_link is None:
                raise Exception('cap_link is None')

            if not validators.url(cap_link):
                # TODO: Track this?
                logger.warning(f'Invalid url {cap_link}')
                continue

            alert_urls.add(url)

            # skip if alert has been processed before
            if ProcessedAlert.objects.filter(url=url).exists() or Alert.objects.filter(url=url).exists():
                continue

            # navigate alert
            success, alert_root = fetch_alert_using_url(cap_link)
            if not success:
                continue

            if get_alert(url, alert_root, feed, ns):
                polled_alerts_count += 1
        except Exception:
            logger.error(
                '[NWS_US] Failed to fetch url',
                exc_info=True,
                extra=logger_log_extra(
                    {
                        'url': url,
                        'alert_entry': str(alert_entry),
                    }
                ),
            )
        else:
            valid_poll = True

    return alert_urls, polled_alerts_count, valid_poll
