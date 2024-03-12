import xml.etree.ElementTree as ET

import requests

from apps.cap_feed.formats.cap_xml import get_alert
from apps.cap_feed.formats.utils import (
    log_attributeerror,
    log_requestexception,
    log_valueerror,
)
from apps.cap_feed.models import Alert, ProcessedAlert


# processing for nws_us format, example: https://api.weather.gov/alerts/active
def get_alerts_nws_us(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = requests.get(feed.url, headers={'Accept': 'application/atom+xml'})
    except requests.exceptions.RequestException as e:
        log_requestexception(feed, e, None)
        return alert_urls, polled_alerts_count, valid_poll
    root = ET.fromstring(response.content)
    for alert_entry in root.findall('atom:entry', ns):
        try:
            url = alert_entry.find('atom:id', ns).text
            alert_urls.add(url)
            cap_link = alert_entry.find('atom:link', ns).attrib['href']
            # skip if alert has been processed before
            if ProcessedAlert.objects.filter(url=url).exists() or Alert.objects.filter(url=url).exists():
                continue
            alert_response = requests.get(cap_link)
            # navigate alert
            alert_root = ET.fromstring(alert_response.content)
            polled_alert_count = get_alert(url, alert_root, feed, ns)
            polled_alerts_count += polled_alert_count
        except requests.exceptions.RequestException as e:
            log_requestexception(feed, e, url)
        except AttributeError as e:
            log_attributeerror(feed, e, url)
        except ValueError as e:
            log_valueerror(feed, e, url)
        else:
            valid_poll = True

    return alert_urls, polled_alerts_count, valid_poll
