import logging
import typing
import xml.etree.ElementTree as ET
from datetime import datetime

import pytz
import requests

from apps.cap_feed.models import FeedLog

logger = logging.getLogger(__name__)


# converts CAP1.2 iso format datetime string to datetime object in UTC timezone
def convert_datetime(original_datetime):
    if original_datetime is None:
        return None
    return datetime.fromisoformat(original_datetime).astimezone(pytz.timezone('UTC'))


def fetch_alert_using_url(url) -> tuple[typing.Literal[False], None] | tuple[typing.Literal[True], ET.Element]:
    # navigate alert
    alert_response = requests.get(url)
    alert_response_content = alert_response.content
    if alert_response.status_code != 200:
        logger.warning(f'Skipping for url {url}: Invalid status_code {alert_response.status_code}')
        return False, None

    if alert_response_content is None or alert_response_content.strip() == '':
        logger.warning(f'Skipping for url {url}: Due to empty content')
        return False, None

    return True, ET.fromstring(alert_response_content)


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
