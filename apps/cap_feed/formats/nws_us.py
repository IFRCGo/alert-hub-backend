import logging
import xml.etree.ElementTree as ET

import requests

from apps.cap_feed.formats.cap_xml import get_alert
from apps.cap_feed.models import Alert, ProcessedAlert
from utils.common import logger_log_extra

logger = logging.getLogger(__name__)


# processing for nws_us format, example: https://api.weather.gov/alerts/active
def get_alerts_nws_us(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = requests.get(feed.url, headers={'Accept': 'application/atom+xml'})
    except requests.exceptions.RequestException:
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
            alert_urls.add(url)

            cap_link_element = alert_entry.find('atom:link', ns)
            if cap_link_element is None:
                raise Exception('atom:link not found')
            cap_link = cap_link_element.attrib['href']
            if cap_link is None:
                raise Exception('cap_link is None')

            # skip if alert has been processed before
            if ProcessedAlert.objects.filter(url=url).exists() or Alert.objects.filter(url=url).exists():
                continue

            alert_response = requests.get(cap_link)
            # navigate alert
            alert_root = ET.fromstring(alert_response.content)
            polled_alert_count = get_alert(url, alert_root, feed, ns)
            polled_alerts_count += polled_alert_count
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
