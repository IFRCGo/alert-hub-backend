from django.core.cache import cache
from .models import CapFeedRegion



def initialise_region_cache():
    regions_data = {'regions': []}
    regions = CapFeedRegion.objects.all()
    for region in regions:
        region_data = region.to_dict()
        region_data['countries'] = []
        countries = region.capfeedcountry_set.all()
        for country in countries:
            for admin1 in country.capfeedadmin1_set.all():
                if admin1.capfeedalertadmin1_set.count() > 0:
                    region_data['countries'].append(country.to_dict())
                    break
        if len(region_data['countries']) > 0:
            regions_data['regions'].append(region_data)

    cache.set("regions", regions_data, timeout = None)
    
def get_regions():
    regions_cache_key = "regions"
    return cache.get(regions_cache_key, {})
