from django.core.cache import cache
from .models import CapFeedCountry, CapFeedAlert
from django.utils import timezone



def calculate_country(country):
    country_data = {
            'country_id' : country.id,
            'country_name' : country.name,
            'admin1s' : []
            }
    for admin1 in country.capfeedadmin1_set.all():
        filters = {'urgency': set(), 'severity': set(), 'certainty': set()}
        for alert_admin1 in admin1.capfeedalertadmin1_set.all():
            alert = alert_admin1.alert
            for info in alert.capfeedalertinfo_set.all():
                filters['urgency'].add(info.urgency)
                filters['severity'].add(info.severity)
                filters['certainty'].add(info.certainty)
        filters['urgency'] = list(filters['urgency'])
        filters['severity'] = list(filters['severity'])
        filters['certainty'] = list(filters['certainty'])
        if admin1.capfeedalertadmin1_set.count() > 0:
            admin1_data = admin1.to_dict()
            admin1_data['filters'] = filters
            country_data['admin1s'].append(admin1_data)
        
    cache.set("country" + str(country.id), country_data, timeout = None)


def update_country_cache():
    print('Updating country_admin1s cache...')

    update_records = cache.get('update_records', dict())
    cache_records = cache.get('country_cache_records', dict())
    old_country_ids = set()
    for country_id in update_records:
        cap_update_time = update_records[country_id]
        cache_update_time = cache_records.get(country_id, None)
        if (cache_update_time is None) or (cache_update_time < cap_update_time):
            try:
                country = CapFeedCountry.objects.get(id=country_id)
                print(f'Updating country cache for {country.name}')
                calculate_country(country)
                cache_records[country_id] = timezone.now()
            except:
                old_country_ids.add(country_id)
    cache.set('country_cache_records', cache_records, timeout = None)

    # Remove old country ids
    update_records = cache.get('update_records', dict())
    cache_records = cache.get('country_cache_records', dict())
    for old_country_id in old_country_ids:
        update_records.pop(old_country_id)
        cache_records.pop(old_country_id)
    cache.set('update_records', update_records, timeout = None)
    cache.set('country_cache_records', cache_records, timeout = None)

def get_country(country_id):
    country_cache_key = "country" + str(country_id)
    return cache.get(country_cache_key, {})
