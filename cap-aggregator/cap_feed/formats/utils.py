import pytz
from datetime import datetime
from cap_feed.models import FeedLog



# converts CAP1.2 iso format datetime string to datetime object in UTC timezone
def convert_datetime(original_datetime):
    if original_datetime is None:
        return None
    return datetime.fromisoformat(original_datetime).astimezone(pytz.timezone('UTC'))

def log_requestexception(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'RequestException'
    log.error_message = e
    log.description = 'It is likely that connection to this feed is unstable or the cap aggregator has been blocked by the feed server.'
    log.response = ('Check that the feed is online and stable.\n'
    + 'If the feed is stable, the cap aggregator may have been blocked after too many requests. This is likely temporary but increasing the polling interval may help prevent this in the future.')
    if url:
        log.alert_url = url
    log.save()

def log_attributeerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'AttributeError'
    log.error_message = e
    log.description = 'It is likely that the feed structure has changed and the corresponding feed format needs to be updated.'
    log.response = 'Check that the corresponding feed format is able to navigate the feed structure and extract the necessary data.'
    if url:
        log.alert_url = url
    log.save()

def log_integrityerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'IntegrityError'
    log.error_message = e
    log.description = 'This is caused by a violation of the Alert schema.'
    log.response = ('Check that the xml elements of the alert contains valid data according to CAP-v1.2 schema.\n'
    + 'For example, the content of a <polygon> tag cannot be empty since the CAP aggregator expects valid data inside this optional tag if it is found.')
    log.alert_url = url
    log.save()

def log_valueerror(feed, e, url):
    log = FeedLog()
    log.feed = feed
    log.exception = 'ValueError'
    log.error_message = e
    log.description = 'This is caused by a violation of the Alert schema.'
    log.response = ('Check that the xml elements of the alert contains valid data according to CAP-v1.2 schema.\n'
    + 'For example, alphabetic timezone designators such as "Z" must not be used.  The timezone for UTC must be represented as "-00:00".')
    log.alert_url = url
    log.save()