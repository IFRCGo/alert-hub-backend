import time

import httpx
import typing_extensions
from django.core.management.base import BaseCommand

from apps.cap_feed.models import Country
from apps.cap_feed.utils import CountryCache


# NOTE: This is run automatically using celery schedule job
class Command(BaseCommand):
    @typing_extensions.override
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country_cache = CountryCache()

    def _get_country_api_map(self) -> dict[int, str]:
        self.stdout.write("Fetching countries data..")
        resp = httpx.get("https://preparemessages.ifrc.org/api/organisations")
        resp.raise_for_status()
        api_country_map = {}
        for country_data in resp.json()["data"]:
            country_code = country_data["countryCode"]
            db_country = self.country_cache.get_country_by_iso3(country_code)
            if db_country is None:
                continue
            api_country_map[db_country.pk] = country_code
        return api_country_map

    def _country_has_messages(self, country_code: str, retry: int = 0) -> bool:
        # To avoid 429 Too Many Requests
        resp = httpx.get(f"https://preparemessages.ifrc.org/api/organisations/{country_code}/instructions")
        if resp.status_code == 429:
            if retry > 5:
                raise Exception("To many '429 Too Many Requests' from the server")
            # Try again after few seconds
            self.stdout.write("\t- Got '429 Too Many Requests' from server.. waiting for 10 seconds before continuing")
            time.sleep(10)
            return self._country_has_messages(country_code, retry=retry + 1)

        resp.raise_for_status()
        return len(resp.json()["data"]) > 0

    def handle(self, *_, **options):
        country_api_map = self._get_country_api_map()
        country_api_map_len = len(country_api_map)

        self.stdout.write(f"Country data to fetch {country_api_map_len}")
        db_countries_with_messages_id = []
        for idx, (db_country_id, what_now_country_code) in enumerate(country_api_map.items(), start=1):
            self.stdout.write(f"({idx:3}/{country_api_map_len}) Fetching country data.. {what_now_country_code}")
            if self._country_has_messages(what_now_country_code):
                self.stdout.write("\t- Has messages")
                db_countries_with_messages_id.append(db_country_id)

        self.stdout.write("Updating database")
        # Flag as has messages
        Country.objects.filter(
            pk__in=db_countries_with_messages_id,
            has_preparedness_messages=False,
        ).update(has_preparedness_messages=True)

        # Flag as doesn't messages
        Country.objects.exclude(
            pk__in=db_countries_with_messages_id,
            has_preparedness_messages=True,
        ).update(has_preparedness_messages=False)
