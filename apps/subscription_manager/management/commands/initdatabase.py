from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.subscription_manager.subscription_alert_mapping import (
    map_subscriptions_to_alert,
)


class Command(BaseCommand):
    help = "Starting inputting alerts from alert database into subscription database"

    def handle(self, *args, **options):
        cache.clear()
        print("Clear Cache")
        # Converting all alerts in alert database into subscription database
        map_subscriptions_to_alert()
        print("All alerts data in alert database has been mapped with each subscription.")
