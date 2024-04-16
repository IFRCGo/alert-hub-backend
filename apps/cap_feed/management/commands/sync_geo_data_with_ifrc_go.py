from django.core.management.base import BaseCommand

from apps.cap_feed.data_injector.geo import IfrcGoGeoInjector


class Command(BaseCommand):

    def handle(self, *_, **options):
        self.stdout.write('Starting geo data sync...')
        IfrcGoGeoInjector(django_cmd=self).sync()
