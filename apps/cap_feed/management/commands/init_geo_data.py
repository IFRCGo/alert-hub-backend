from django.core.management.base import BaseCommand

from apps.cap_feed.data_injector.geo import inject_geographical_data


class Command(BaseCommand):

    def handle(self, *_, **options):
        self.stdout.write('Initiating geo data...')
        inject_geographical_data()
