import logging
import signal
import time
import typing

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandParser
from django.db import connections
from django.db.utils import OperationalError
from kombu.exceptions import OperationalError as KombuOperationalError
from redis.exceptions import ConnectionError as RedisConnectionError

from main.celery import app as celery_app

logger = logging.getLogger(__name__)


class TimeoutException(Exception): ...  # noqa: E701


def timeout_handler(*_):
    raise Exception("The command timed out.")


class Command(BaseCommand):
    help = "Wait for resources our application depends on"

    def wait_for_db(self):
        self.stdout.write("Waiting for DB...")
        db_conn = None
        start_time = time.time()
        while True:
            try:
                db_conn = connections["default"]
                db_conn.ensure_connection()
                break
            except OperationalError:
                ...
            # Try again
            self.stdout.write(self.style.WARNING("DB not available, waiting..."))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"DB is available after {time.time() - start_time:.5f} seconds"))

    def wait_for_redis(self):
        self.stdout.write("Waiting for Redis...")
        redis_conn = None
        start_time = time.time()
        while True:
            try:
                cache.set("wait-for-it-ping", "pong", timeout=1)  # Set a key to check Redis availability
                redis_conn = cache.get("wait-for-it-ping")  # Try to get the value back from Redis
                if redis_conn != "pong":
                    raise TypeError
                break
            except (RedisConnectionError, TypeError):
                ...
            # Try again
            self.stdout.write(self.style.WARNING("Redis not available, waiting..."))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"Redis is available after {time.time() - start_time:.5f} seconds"))

    def wait_for_rabbitmq(self):
        self.stdout.write("Waiting for RabbitMQ...")
        broker_url = getattr(settings, "CELERY_BROKER_URL", None)
        if not broker_url:
            self.stdout.write(self.style.WARNING("No CELERY_BROKER_URL provided. Skipping wait"))
            return

        start_time = time.time()
        while True:
            try:
                # Try to acquire a broker connection
                with celery_app.connection_for_write() as conn:
                    conn.ensure_connection(max_retries=1)  # just try once per loop
                break
            except KombuOperationalError as ex:
                logger.warning("RabbitMQ error: %s", ex)
            self.stdout.write(self.style.WARNING("RabbitMQ not available, waiting..."))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"RabbitMQ is available after {time.time() - start_time:.5f} seconds"))

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--timeout",
            "--timeout",
            type=int,
            default=600,
            help="The maximum time (in seconds) the command is allowed to run before timing out. Default is 10 min.",
        )
        parser.add_argument("--db", action="store_true", help="Wait for DB to be available")
        parser.add_argument("--redis", action="store_true", help="Wait for Redis to be available")
        parser.add_argument("--rabbitmq", action="store_true", help="Wait for RabbitMQ to be available")
        parser.add_argument("--all", action="store_true", help="Wait for all to be available")

    def handle(self, **kwargs: typing.Any):
        timeout = kwargs["timeout"]
        _all = kwargs["all"]

        # Set the timeout handler (1 minute = 60 seconds)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            if _all or kwargs["db"]:
                self.wait_for_db()
            if _all or kwargs["redis"]:
                self.wait_for_redis()
            if _all or kwargs["rabbitmq"]:
                self.wait_for_rabbitmq()
        except TimeoutException:
            ...
        finally:
            # Disable the alarm (cleanup)
            signal.alarm(0)
