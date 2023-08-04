from django.core.cache import cache
from .models import CapFeedCountry



def initialise_country_cache():
    countries = CapFeedCountry.objects.all()
    for country in countries:
        country_data = {
            'country_id' : country.id,
            'country_name' : country.name,
            'admin1s' : []
            }
        for admin1 in country.capfeedadmin1_set.all():
            if admin1.capfeedalertadmin1_set.count() > 0:
                country_data['admin1s'].append(admin1.to_dict())
        
        cache.set("country" + str(country.id), country_data, timeout = None)

def get_country(country_id):
    country_cache_key = "country" + str(country_id)
    return cache.get(country_cache_key, {})