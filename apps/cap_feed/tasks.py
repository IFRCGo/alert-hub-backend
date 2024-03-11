from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django.utils import timezone

from .models import Alert, AlertInfo, Feed, ProcessedAlert
from .formats import format_handler as fh
from . import data_injector as di


@shared_task
def poll_feed(url):
    polled_alerts_count = 0
    try:
        feed = Feed.objects.get(url=url)
        if not feed.enable_polling:
            return f"Feed with url {url} is disabled for polling"
        polled_alerts_count += fh.get_alerts(feed)
        return f"polled {polled_alerts_count} alerts from {feed.url}"
    except Feed.DoesNotExist:
        return f"Feed with url {url} does not exist"


@shared_task
def remove_expired_alerts():
    # Remove valid alerts that have expired
    AlertInfo.objects.filter(expires__lt=timezone.now()).delete()
    expired_alerts = Alert.objects.filter(infos__isnull=True)
    expired_alerts_count = expired_alerts.count()
    expired_alerts.delete()
    return f"removed {expired_alerts_count} alerts"


@shared_task
def remove_expired_alert_records():
    # Remove records of expired alerts
    ProcessedAlert.objects.filter(expires__lt=timezone.now()).delete()
    return "removed records of expired alerts"


@shared_task
def inject_data():
    di.inject_geographical_data()
    di.inject_feeds()
    return "injected data"
