import sys

from django.apps import AppConfig
from django.db.models.signals import post_save


class AlertCacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alert_cache'

    def ready(self):
        from .cache import cache_alert,cache_country,cache_startup
        if 'collectstatic' not in sys.argv or 'migrate' not in sys.argv or 'makemigrations' not \
                in sys.argv:
            is_locked = cache_startup()
            if is_locked == True:
                print("a ha ha")
                #cache_alert()
                #cache_country()