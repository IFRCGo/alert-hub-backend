from django.apps import AppConfig
from django.db.models.signals import post_save


class AlertCacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alert_cache'

    def ready(self):
        from .cache import cache_alert,cache_country
        cache_alert()
        cache_country()