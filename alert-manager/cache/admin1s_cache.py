from django.core.cache import cache
from .models import CapFeedFeed, CapFeedCountry



def update_admin1s_cache():
    print('Updating admin1s cache...')
    admin1s_data = {'countries': []}
    country_ids = set(CapFeedFeed.objects.values_list('country', flat=True))
    for country_id in country_ids:
        try:
            country = CapFeedCountry.objects.get(id=country_id)
        except CapFeedCountry.DoesNotExist:
            continue
        country_data = {'id': country.id, 'name': country.name, 'admin1s': []}
        for district in country.capfeedadmin1_set.all():
            district_data = {'id': district.id, 'name': district.name}
            country_data['admin1s'].append(district_data)
        admin1s_data['countries'].append(country_data)

    cache.set("admin1s", admin1s_data, timeout = None)

def get_admin1s():
    admin1s_cache_key = "admin1s"
    return cache.get(admin1s_cache_key, {})
