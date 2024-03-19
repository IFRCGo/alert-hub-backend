import os
from datetime import timedelta

from celery import Celery
from kombu import Queue

# TODO: Merge main.settings and main.production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

app = Celery('main')

app.conf.beat_schedule = {
    'remove_expired_alerts': {
        'task': 'apps.cap_feed.tasks.remove_expired_alerts',
        'schedule': timedelta(minutes=1),
        'options': {'queue': 'default'},
    },
    'remove_expired_alert_records': {
        'task': 'apps.cap_feed.tasks.remove_expired_alert_records',
        'schedule': timedelta(days=1),
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
app.conf.task_queues = (
    Queue('default', routing_key='poll.#', exchange='poll'),
    Queue('inject', routing_key='inject.#', exchange='inject'),
)
app.conf.task_default_exchange = 'poll'
app.conf.task_default_exchange_type = 'topic'
app.conf.task_default_routing_key = 'poll.default'

task_routes = {
    'apps.cap_feed.tasks.poll_feed': {
        'queue': 'default',
        'routing_key': 'poll.#',
        'exchange': 'poll',
    },
    'apps.cap_feed.tasks.remove_expired_alerts': {
        'queue': 'default',
        'routing_key': 'poll.#',
        'exchange': 'poll',
    },
    'apps.cap_feed.tasks.inject_data': {
        'queue': 'inject',
        'routing_key': 'inject.#',
        'exchange': 'inject',
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
