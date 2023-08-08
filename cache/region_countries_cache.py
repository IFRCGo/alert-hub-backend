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
        if len(region_data['countries']) > 0:
            regions_data['regions'].append(region_data)

    cache.set("regions", regions_data, timeout = None)
    
def get_regions():
    regions_cache_key = "regions"
    return cache.get(regions_cache_key, {})
