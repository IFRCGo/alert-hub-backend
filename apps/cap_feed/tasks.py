from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from django.db import models
from django.utils import timezone

from main.cache import CacheKey
from utils.common import RuntimeProfile, redis_lock

from .formats import format_handler as fh
from .models import Alert, Feed, ProcessedAlert

logger = logging.getLogger(__name__)


# NOTE: This is used by apps/cap_feed/receivers
@shared_task
def poll_feed(pk: int):
    with redis_lock(CacheKey.RedisLockKey.POLL_FEED.format(pk)) as acquired:
        if not acquired:
            logger.warning(f'Feed pool for id: {pk} is already running')
            return
        polled_alerts_count = 0
        try:
            feed = Feed.objects.get(pk=pk)
            if not feed.enable_polling:
                return f"Feed with url {feed.url} is disabled for polling"
            with RuntimeProfile(f"Feed: {feed.url} alerts pull"):
                polled_alerts_count += fh.get_alerts(feed)
            return f"polled {polled_alerts_count} alerts from {feed.url}"
        except Feed.DoesNotExist:
            return f"Feed with ID: {pk} does not exist"


@shared_task
def tag_expired_alerts():
    with redis_lock(CacheKey.RedisLockKey.TAG_EXPIRE_ALERT) as acquired:
        if not acquired:
            logger.warning('Tag expired is already running')
            return
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
    with redis_lock(CacheKey.RedisLockKey.REMOVE_EXPIRE_PROCESSED_ALERT) as acquired:
        if not acquired:
            logger.warning('Remove expired processed alert is already running')
            return
        # Remove records of expired alerts
        ProcessedAlert.objects.filter(expires__lt=timezone.now()).delete()
        return "removed records of expired alerts"
