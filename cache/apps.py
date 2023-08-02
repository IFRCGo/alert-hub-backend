import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class CacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cache'

    def ready(self):
        from .region_cache import initialise_region_cache
        from .alert_cache import initialise_alert_cache
        from .country_cache import initialise_countries_cache
        from django.core.cache import cache
        #For local
        if 'runserver' in sys.argv:
        #For production
        #if 'collectstatic' not in sys.argv or 'migrate' not in sys.argv or 'makemigrations' not \
        #        in sys.argv:
            is_locked = cache.add("locked", True, 5)
            if is_locked == True:
                initialise_alert_cache()
                initialise_region_cache()
                initialise_countries_cache()

