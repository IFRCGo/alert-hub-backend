import os
import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class CacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cache'

    def ready(self):
        from .countries_cache import initialise_countries_cache
        from .districts_cache import initialise_districts_cache
        from .alerts_cache import initialise_alerts_cache
        from .polygons_cache import initialise_polygons_cache
        from django.core.cache import cache
        #For local
        is_locked = cache.add("locked", True, 5)
        if is_locked == True:
            if 'WEBSITE_HOSTNAME' in os.environ and 'collectstatic' not in sys.argv \
                and 'migrate' not in sys.argv or ('WEBSITE_HOSTNAME' not in os.environ
                    and 'runserver' in sys.argv):
                print('Initialising countries cache...')
                initialise_countries_cache()
                print('Initialising districts cache...')
                initialise_districts_cache()
                print('Initialising alerts cache...')
                initialise_alerts_cache()
                print('Initialising polygons cache...')
                initialise_polygons_cache()
                