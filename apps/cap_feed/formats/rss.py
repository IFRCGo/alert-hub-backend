import logging
import xml.etree.ElementTree as ET

import httpx
import validators

from apps.cap_feed.formats.cap_xml import get_alert
from apps.cap_feed.models import Alert, Feed, ProcessedAlert
from utils.common import logger_log_extra

from .utils import COMMON_REQUESTS_HEADERS, fetch_alert_using_url

logger = logging.getLogger(__name__)


# processing for rss format, example: https://cap-sources.s3.amazonaws.com/mg-meteo-en/rss.xml
def get_alerts_rss(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = httpx.get(
            feed.url,
            headers=COMMON_REQUESTS_HEADERS,
            timeout=Feed.MAX_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.error(
            '[RSS] Failed to fetch feed alerts',
            exc_info=True,
            extra=logger_log_extra(
                {
                    'feed': feed.pk,
                }
            ),
        )
        return alert_urls, polled_alerts_count, valid_poll

    root = ET.fromstring(response.content)
    alert_entries_element = root.find('channel')
    if alert_entries_element is None:
        return alert_urls, polled_alerts_count, valid_poll

    for alert_entry in alert_entries_element.findall('item'):
        url = None
        try:
            url_element = alert_entry.find('link')
            if url_element is None:
                raise Exception('link not found')
            url = url_element.text
            if url is None:
                raise Exception('URL is None')

            if not validators.url(url):
                # TODO: Track this?
                logger.warning(f'Invalid url {url}')
                continue

            alert_urls.add(url)
            # skip if alert has been processed before
            if ProcessedAlert.objects.filter(url=url).exists() or Alert.objects.filter(url=url).exists():
                continue

            # navigate alert
            success, alert_root = fetch_alert_using_url(url)
            if not success:
                continue

            if get_alert(url, alert_root, feed, ns):
                polled_alerts_count += 1

        except Exception:
            logger.error(
                '[RSS] Failed to fetch url',
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
