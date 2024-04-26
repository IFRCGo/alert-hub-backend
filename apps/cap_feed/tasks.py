from __future__ import absolute_import, unicode_literals

from celery import shared_task
from django.db import models
from django.utils import timezone

from .data_injector.feed import inject_feeds
from .data_injector.geo import inject_geographical_data
from .formats import format_handler as fh
from .models import Alert, Feed, ProcessedAlert


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
    # Tag valid alerts that have expired
    expired_alerts = (
        Alert.objects.filter(is_expired=False)
        .annotate(
            active_alert_info_count=models.Count(
                'infos',
                filter=models.Q(
                    infos__expires__gt=timezone.now(),
                ),
            ),
        )
        .filter(active_alert_info_count=0)
    )

    expired_alerts_count = expired_alerts.count()
    expired_alerts.update(is_expired=True)

    return f"Tag {expired_alerts_count} alerts as expired"


@shared_task
def remove_expired_alert_records():
    # Remove records of expired alerts
    ProcessedAlert.objects.filter(expires__lt=timezone.now()).delete()
    return "removed records of expired alerts"


# TODO: Add this to management command
@shared_task
def inject_data():
    inject_geographical_data()
    inject_feeds()
    return "injected data"
