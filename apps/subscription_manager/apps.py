import os
import sys

from django.apps import AppConfig


class SubscriptionManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.subscription_manager'

    def ready(self):
        if ('WEBSITE_HOSTNAME' in os.environ and 'migrate' not in sys.argv and 'collectstatic'
            not in sys.argv) \
                or \
                ('WEBSITE_HOSTNAME' not in os.environ and 'runserver' in sys.argv):
            pass
            #Used for testing locks
            #from .subscription_alert_mapping import map_subscription_to_alert, \
            #    map_alert_to_subscription, delete_alert_to_subscription
            #from django.core.cache import cache
            #cache.clear()
            #map_subscription_to_alert(3)
            #delete_alert_to_subscription(3408)
