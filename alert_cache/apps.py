import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class AlertCacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alert_cache'

    def ready(self):
        from .cache import initialise_region_cache, cache_startup, initialise_alerts_cache
        if 'collectstatic' not in sys.argv or 'migrate' not in sys.argv or 'makemigrations' not \
                in sys.argv:
            is_locked = cache_startup()
            if is_locked == True:
                initialise_alerts_cache()
                initialise_region_cache()
