from django.core.cache import cache
from .models import CapFeedFeed, CapFeedCountry



def initialise_admin1s_cache():
    districts_data = {'countries': []}
    country_ids = set(CapFeedFeed.objects.all().values_list('country', flat=True))
    for country_id in country_ids:
        country = CapFeedCountry.objects.get(id=country_id)
        country_data = {'id': country.id, 'name': country.name, 'districts': []}
        for district in country.capfeedadmin1_set.all():
            district_data = {'id': district.id, 'name': district.name}
            country_data['districts'].append(district_data)
        districts_data['countries'].append(country_data)

    cache.set("districts", districts_data, timeout = None)

def get_admin1s():
    districts_cache_key = "districts"
    return cache.get(districts_cache_key, {})
