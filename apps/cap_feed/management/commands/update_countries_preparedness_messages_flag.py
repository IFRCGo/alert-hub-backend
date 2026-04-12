import logging

import httpx
import typing_extensions
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.cap_feed.models import Country
from apps.cap_feed.utils import CountryCache

logger = logging.getLogger(__name__)


# NOTE: This is run automatically using celery schedule job
class Command(BaseCommand):
    @typing_extensions.override
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country_cache = CountryCache()

    def get_countries_id_with_messages(self) -> list[int]:
        self.stdout.write("Fetching countries data")
        resp = httpx.get(
            # NOTE: This endpoint doesn't require token unlike other
            f"{settings.PREPAREMESSAGES_API_DOMAIN}/v2/org",
            params={
                "published": True,
            },
        )
        countries_data = resp.json()["data"]

        db_countries_with_messages_id = []
        for country_data in countries_data:
            country_code = country_data["countryCode"]
            db_country = self.country_cache.get_country_by_iso3(country_code)
            if db_country is None:
                logger.warning("Remote countryCode missing in DB: %s", country_code)
                continue
            db_countries_with_messages_id.append(db_country.pk)

        return db_countries_with_messages_id

    def show_db_state(self, prefix: str):
        with_message_qs = Country.objects.filter(has_preparedness_messages=True)
        without_message_qs = Country.objects.filter(has_preparedness_messages=False)
        self.stdout.write(f"{prefix}Countries with has_preparedness_messages: {without_message_qs.count()}")
        self.stdout.write(f"{prefix}Countries without has_preparedness_messages: {with_message_qs.count()}")

    def handle(self, *_, **options):
        self.show_db_state("(Before) ")
        db_countries_with_messages_id = self.get_countries_id_with_messages()

        self.stdout.write("Updating database")
        self.stdout.write(f"Marking {len(db_countries_with_messages_id)} with has_preparedness_messages")
        # Flag as has messages
        Country.objects.filter(
            pk__in=db_countries_with_messages_id,
            has_preparedness_messages=False,
        ).update(has_preparedness_messages=True)

        self.stdout.write("Marking other without has_preparedness_messages")
        # Flag as doesn't messages
        Country.objects.exclude(
            pk__in=db_countries_with_messages_id,
            has_preparedness_messages=True,
        ).update(has_preparedness_messages=False)

        self.show_db_state("(After) ")
