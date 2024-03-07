from django.core.management.base import BaseCommand
from subscription_manager_dir.subscription_alert_mapping import map_subscriptions_to_alert
from django.core.cache import cache

class Command(BaseCommand):
    help = "Starting inputting alerts from alert database into subscription database"

    def handle(self, *args, **options):
        cache.clear()
        print("Clear Cache")
        # Converting all alerts in alert database into subscription database
        map_subscriptions_to_alert()
        print("All alerts data in alert database has been mapped with each subscription.")

