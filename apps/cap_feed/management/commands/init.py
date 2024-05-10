from django.core.management.base import BaseCommand

from apps.cap_feed.data_injector.feed import inject_feeds
from apps.cap_feed.data_injector.geo import IfrcGoGeoInjector


class Command(BaseCommand):

    def handle(self, *_, **options):
        self.stdout.write('Initiating feeds...')
        IfrcGoGeoInjector(django_cmd=self).sync()
        inject_feeds()
