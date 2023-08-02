import json

from django.core.cache import cache
from .models import CapFeedCountry

def initialise_countries_cache():
    countries = CapFeedCountry.objects.all()
    for country in countries:
        cache.set("country"+str(country.id), json.dumps(country.to_dict(), indent=None),
                  timeout=None)


def get_alerts_by_country(country_id):
    cache_keys = cache.client.keys('*')
    country_cache_key = "country" + str(country_id)
    if country_cache_key in cache_keys:
        return cache.get(country_cache_key)
    else:
        return f"Country {country_id} is not found!"
