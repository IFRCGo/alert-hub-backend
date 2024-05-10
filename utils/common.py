import copy
import datetime
import functools
import logging
import re
import time
import typing
from contextlib import contextmanager

from django.conf import settings
from django.db import models

from main.cache import cache

logger = logging.getLogger(__name__)


# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def to_camel_case(snake_str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


def to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_queryset_for_model(
    model: typing.Type[models.Model],
    queryset: models.QuerySet | None = None,
) -> models.QuerySet:
    if queryset is not None:
        return copy.deepcopy(queryset)
    return model.objects.all()


def logger_log_extra(context_data):
    return {
        'context': context_data,
    }


@contextmanager
def redis_lock(lock_id: str):
    timeout_at = time.monotonic() + settings.REDIS_LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, 1, settings.REDIS_LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)


class RuntimeProfile:
    label: str
    start: typing.Optional[datetime.datetime]

    def __init__(self, label: str = 'N/A'):
        self.label = label
        self.start = None

    def __call__(self, func):
        self.label = func.__name__

        @functools.wraps(func)
        def decorated(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return decorated

    def __enter__(self):
        self.start = datetime.datetime.now()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        assert self.start is not None
        time_delta = datetime.datetime.now() - self.start
        logger.info(f'Runtime with <{self.label}>: {time_delta}')
