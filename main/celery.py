import logging
import os
from datetime import timedelta

import celery
import httpx
from celery.schedules import crontab
from django.conf import settings
from kombu import Queue

from main import sentry

logger = logging.getLogger(__name__)


class Celery(celery.Celery):
    def on_configure(self):  # type: ignore[reportIncompatibleVariableOverride]
        if settings.SENTRY_ENABLED:
            sentry.init_sentry(**settings.SENTRY_CONFIG)


# TODO: Merge main.settings and main.production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')


app = Celery('main')

INTERNAL_CELERY_TASK_NAME_PREFIX = 'alert_hub_'


class TimeConstants:
    SECONDS_IN_A_DAY = 24 * 60 * 60
    SECONDS_IN_A_HOUR = 60 * 60
    SECONDS_IN_A_WEEK = 7 * 24 * 60 * 60
    SECONDS_IN_A_MINUTE = 60


# TODO: Sync this with the database, don't overwrite enabled flag (show warning), add a command?
app.conf.beat_schedule = {
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}tag_expired_alerts': {
        'task': 'apps.cap_feed.tasks.tag_expired_alerts',
        'schedule': timedelta(minutes=1),
        'options': {
            'queue': 'default',
            'expire_seconds': TimeConstants.SECONDS_IN_A_MINUTE,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}remove_expired_alert_records': {
        'task': 'apps.cap_feed.tasks.remove_expired_alert_records',
        'schedule': timedelta(days=1),
        'options': {
            'queue': 'default',
            'expire_seconds': TimeConstants.SECONDS_IN_A_DAY,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}process_pending_subscription_alerts': {
        'task': 'apps.subscription.tasks.process_pending_subscription_alerts',
        'schedule': timedelta(minutes=10),
        'options': {
            'queue': 'default',
            'expire_seconds': 10 * TimeConstants.SECONDS_IN_A_MINUTE,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}send_daily_user_alert_subscriptions_email': {
        'task': 'apps.subscription.tasks.send_daily_user_alert_subscriptions_email',
        'schedule': timedelta(days=1),
        'options': {
            'queue': 'default',
            'expire_seconds': TimeConstants.SECONDS_IN_A_DAY,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}send_weekly_user_alert_subscriptions_email': {
        'task': 'apps.subscription.tasks.send_weekly_user_alert_subscriptions_email',
        'schedule': crontab(minute=1, hour=1, day_of_week='monday'),
        'options': {
            'queue': 'default',
            'expire_seconds': TimeConstants.SECONDS_IN_A_WEEK,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}send_monthly_user_alert_subscriptions_email': {
        'task': 'apps.subscription.tasks.send_monthly_user_alert_subscriptions_email',
        'schedule': crontab(minute=1, hour=1, day_of_month='1'),
        'options': {
            'queue': 'default',
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}uptime_push': {
        'task': 'main.celery.uptime_push',
        'schedule': timedelta(minutes=30),
        'options': {
            'queue': 'default',
            'expire_seconds': 30 * TimeConstants.SECONDS_IN_A_MINUTE,
        },
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}update_country_preparedness_messages_flag': {
        'task': 'apps.cap_feed.tasks.update_countries_preparedness_messages_flag',
        'schedule': crontab(minute=1, hour=1, day_of_week='monday'),  # NOTE: Needed monthly, but using weekly for now
        'options': {
            'queue': 'default',
        },
    },
}


class CeleryQueue:
    # NOTE: Make sure all queue names are lowercase (They are in k8s)
    default = Queue('default')
    feeds = Queue('feeds')

    ALL_QUEUE = (
        default,
        feeds,
    )


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.result_expires = settings.CELERY_TASK_EXPIRE
app.conf.task_default_queue = CeleryQueue.default.name

app.conf.task_queues = CeleryQueue.ALL_QUEUE

app.conf.task_routes = {
    'apps.cap_feed.tasks.poll_feed': {'queue': CeleryQueue.feeds},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.task(bind=False)
def uptime_push():
    if settings.UPTIME_WORKER_HEARTBEAT:
        httpx.get(settings.UPTIME_WORKER_HEARTBEAT)
