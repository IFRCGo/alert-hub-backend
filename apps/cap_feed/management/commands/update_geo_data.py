from django.core.management.base import BaseCommand

from apps.cap_feed.data_injector.geo import IfrcGoGeoInjector


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-admin1s-sync",
            action="store_true",
            help="Skip Admin1s update",
        )

    def handle(self, *_, **options):
        self.stdout.write("Initiating geo data...")
        skip_admin1s_sync = options.get("skip_admin1s_sync", False)
        IfrcGoGeoInjector(django_cmd=self).sync(
            skip_admin1s_sync=skip_admin1s_sync,
        )
