from cap_feed.models import Alert
from .atom import get_alerts_atom
from .rss import get_alerts_rss
from .nws_us import get_alerts_nws_us



def get_alerts(feed, all_alert_urls=set()):
    # track new alerts
    alert_urls = set()
    # track number of alerts polled
    polled_alerts_count = 0
    # track if poll was valid
    valid_poll = False

    
    print(f'Processing feed: {feed}')
    
    try:
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        match feed.format:
            case "atom":
                alert_urls, polled_alerts_count, valid_poll = get_alerts_atom(feed, ns)
            case "rss":
                alert_urls, polled_alerts_count, valid_poll = get_alerts_rss(feed, ns)
            case "nws_us":
                alert_urls, polled_alerts_count, valid_poll = get_alerts_nws_us(feed, ns)
            case _:
                print(f'Format not supported: {feed}')
                alert_urls, polled_alerts_count, valid_poll = set(), 0, True
    except Exception as e:
        print(f'Error getting alerts from {feed.url}: {e}')
    else:
        if valid_poll:
            # alerts that are in the database and have not expired but are no longer available on the feed must have been deleted by the alerting authority
            # remove these alerts from the database
            all_alert_urls.update(alert_urls)
            deleted_alerts = Alert.objects.filter(feed=feed).exclude(url__in=all_alert_urls)
            deleted_alerts.delete()

    return polled_alerts_count
