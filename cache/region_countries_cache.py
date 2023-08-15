from django.core.cache import cache
from .models import CapFeedRegion



def calculate_country(region_data, country):
    filters = {'urgency': set(), 'severity': set(), 'certainty': set()}
    for alert in country.capfeedalert_set.all():
        for info in alert.capfeedalertinfo_set.all():
            filters['urgency'].add(info.urgency)
            filters['severity'].add(info.severity)
            filters['certainty'].add(info.certainty)
    filters['urgency'] = list(filters['urgency'])
    filters['severity'] = list(filters['severity'])
    filters['certainty'] = list(filters['certainty'])
    if country.capfeedalert_set.count() > 0:
        country_data = country.to_dict()
        country_data['filters'] = filters
        region_data['countries'].append(country_data)
    return region_data


def update_region_cache():
    print('Updating region_countries cache...')
    regions_data = {'regions': []}
    regions = CapFeedRegion.objects.all()
    for region in regions:
        region_data = region.to_dict()
        region_data['countries'] = []
        countries = region.capfeedcountry_set.all()
        for country in countries:
            region_data = calculate_country(region_data, country)
        if len(region_data['countries']) > 0:
            regions_data['regions'].append(region_data)
        
        cache.set("region" + str(region.id), {'regions': [region_data]}, timeout = None)

    cache.set("regions", regions_data, timeout = None)

def get_region(region_id):
    region_cache_key = "region" + str(region_id)
    return cache.get(region_cache_key, {})
    
def get_regions():
    regions_cache_key = "regions"
    return cache.get(regions_cache_key, {})
