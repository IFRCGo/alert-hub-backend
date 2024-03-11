import requests
import xml.etree.ElementTree as ET

from cap_feed.models import Alert, ProcessedAlert
from cap_feed.formats.cap_xml import get_alert
from cap_feed.formats.utils import log_requestexception, log_attributeerror, log_valueerror



# processing for atom format, example: https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-france
def get_alerts_atom(feed, ns):
    alert_urls = set()
    polled_alerts_count = 0
    valid_poll = False

    # navigate list of alerts
    try:
        response = requests.get(feed.url)
    except requests.exceptions.RequestException as e:
        log_requestexception(feed, e, None)
        return alert_urls, polled_alerts_count, valid_poll
    root = ET.fromstring(response.content)
    for alert_entry in root.findall('atom:entry', ns):
        try:
            url = alert_entry.find('atom:id', ns).text
            alert_urls.add(url)
            # skip if alert has been processed before
            if ProcessedAlert.objects.filter(url=url).exists() or Alert.objects.filter(url=url).exists():
                continue
            alert_response = requests.get(url)
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