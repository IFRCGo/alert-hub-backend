import os
import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class CacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cache'

    def ready(self):
        from .region_countries_cache import initialise_region_cache
        from .country_admin1s_cache import initialise_country_cache
        from .admin1_alerts_cache import initialise_admin1_cache
        from .info_areas_cache import initialise_info_cache
        from django.core.cache import cache
        #For local
        is_locked = cache.add("locked", True, 5)
        if is_locked == True:
            if 'WEBSITE_HOSTNAME' in os.environ and 'collectstatic' not in sys.argv \
                and 'migrate' not in sys.argv or ('WEBSITE_HOSTNAME' not in os.environ
                    and 'runserver' in sys.argv):
                print('Initialising region_countries cache...')
                initialise_region_cache()
                print('Initialising country_admin1s cache...')
                initialise_country_cache()
                print('Initialising admin1_alerts cache...')
                initialise_admin1_cache()
                print('Initialising info_areas cache...')
                initialise_info_cache()
                