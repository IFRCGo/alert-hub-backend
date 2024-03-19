from django.core.cache import cache  # pyright: ignore[reportGeneralTypeIssues]
from django_redis.client import DefaultClient

assert type(cache) is DefaultClient
cache: DefaultClient

__all__ = ['cache']
