import json
import logging
import math
import typing

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from main.celery import INTERNAL_CELERY_TASK_NAME_PREFIX

from .models import Country, Feed

logger = logging.getLogger(__name__)


class FeedTaskManager:
    """
    Helper to interact with celery period task management for Feeds
    """

    TASK_NAME_PREFIX = f'{INTERNAL_CELERY_TASK_NAME_PREFIX}poll_feed_'

    @classmethod
    def get_task_name(cls, feed: Feed):
        # XXX: Changing this will require manual changes in the server
        return f'{cls.TASK_NAME_PREFIX}{feed.pk}'

    # TODO: Create a global delete/create configuration
    @classmethod
    def force_delete_all_tasks(cls):
        qs = PeriodicTask.objects.filter(name__startswith=cls.TASK_NAME_PREFIX)
        count = qs.count()
        deleted_items = qs.delete()
        logger.warning(f'Remove {deleted_items}')
        return count

    @classmethod
    def add_task(cls, feed: Feed):
        # XXX: Circular dependency fix
        from .tasks import poll_feed

        interval_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=feed.polling_interval,
            period='seconds',
        )

        try:
            if PeriodicTask.objects.filter(name=cls.get_task_name(feed)).exists():
                logger.warning(f'Periodic task for feed: pk={feed.pk} url={feed.url} already exists')
                return

            if feed.is_archived:
                logger.warning(f'Feed: pk={feed.pk} url={feed.url} is archived')
                return

            PeriodicTask.objects.create(
                name=cls.get_task_name(feed),
                task=f'{poll_feed.__module__}.{poll_feed.__name__}',
                interval=interval_schedule,
                start_time=timezone.now(),
                expire_seconds=feed.polling_interval + 60 * 10,
                kwargs=json.dumps({"pk": feed.pk}),
            )
            logger.info(f'Created periodic task for feed: {feed.url}')
        except Exception:
            logger.error('Error while adding new PeriodicTask', exc_info=True)

    @classmethod
    def remove_task(cls, feed: Feed):
        try:
            deleted_items = PeriodicTask.objects.filter(name=cls.get_task_name(feed)).delete()
            logger.warning(f'Remove {deleted_items} for feed: {feed.url}')
        except Exception:
            logger.warning('[Feed periodic task clean-up] Failed', exc_info=True)

    @classmethod
    def update_task(cls, feed: Feed):
        cls.remove_task(feed)
        cls.add_task(feed)


def distance_to_decimal_degrees(distance: Distance, point: Point):
    # https://gis.stackexchange.com/a/384823
    lat_radians = point.y * (math.pi / 180)  # Where point.y is latitude
    # 1 longitudinal degree at the equator equal 111,319.5m equiv to 111.32km
    return distance.m / (111_319.5 * math.cos(lat_radians))


class CountryCache:
    _countries: list[Country]
    _countries_iso3_map: dict[str, Country]

    def __init__(self):
        self.fetch()

    def fetch(self):
        self._countries = list(Country.objects.all())
        self._countries_iso3_map = {country.iso3.upper(): country for country in self._countries}

    def get_country_by_iso3(self, iso3: str) -> typing.Optional[Country]:
        return self._countries_iso3_map.get(iso3.upper())
