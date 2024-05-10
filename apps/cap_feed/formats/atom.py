import logging
import xml.etree.ElementTree as ET

import requests
import validators

from apps.cap_feed.models import Alert, ProcessedAlert
from utils.common import logger_log_extra

from .cap_xml import get_alert
from .utils import fetch_alert_using_url

logger = logging.getLogger(__name__)


# processing for atom format, example: https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-france
def get_alerts_atom(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = requests.get(feed.url)
    except requests.exceptions.RequestException:
        logger.error(
            '[ATOM] Failed to fetch feed alerts',
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
                '[ATOM] Failed to fetch url',
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
