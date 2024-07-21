from django.core.management.base import BaseCommand

from apps.cap_feed.data_injector.feed import inject_feeds


class Command(BaseCommand):

    def handle(self, *_, **options):
        self.stdout.write('Initiating feeds...')
        inject_feeds()
