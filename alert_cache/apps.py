from django.apps import AppConfig
from django.db.models.signals import post_save


class AlertCacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alert_cache'



