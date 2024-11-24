import logging
import os
from datetime import timedelta

import celery
import requests
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

app.conf.beat_schedule = {
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}tag_expired_alerts': {
        'task': 'apps.cap_feed.tasks.tag_expired_alerts',
        'schedule': timedelta(minutes=1),
        'options': {'queue': 'default'},
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}remove_expired_alert_records': {
        'task': 'apps.cap_feed.tasks.remove_expired_alert_records',
        'schedule': timedelta(days=1),
        'options': {'queue': 'default'},
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}process_pending_subscription_alerts': {
        'task': 'apps.subscription.tasks.process_pending_subscription_alerts',
        'schedule': timedelta(minutes=30),  # TODO: Lower this?
        'options': {'queue': 'default'},
    },
    f'{INTERNAL_CELERY_TASK_NAME_PREFIX}uptime_push': {
        'task': 'main.celery.uptime_push',
        'schedule': timedelta(minutes=30),
        'options': {'queue': 'default'},
    },
}

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.task_default_queue = 'default'
app.conf.task_queues = (Queue('default', routing_key='poll.#', exchange='poll'),)
app.conf.task_default_exchange = 'poll'
app.conf.task_default_exchange_type = 'topic'
app.conf.task_default_routing_key = 'poll.default'
app.conf.result_expires = settings.CELERY_TASK_EXPIRE

task_routes = {
    'apps.cap_feed.tasks.poll_feed': {
        'queue': 'default',
        'routing_key': 'poll.#',
        'exchange': 'poll',
    },
    'apps.cap_feed.tasks.tag_expired_alerts': {
        'queue': 'default',
        'routing_key': 'poll.#',
        'exchange': 'poll',
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@app.task(bind=False)
def uptime_push():
    if settings.UPTIME_WORKER_HEARTBEAT:
        requests.get(settings.UPTIME_WORKER_HEARTBEAT)
