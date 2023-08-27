from django.core.cache import cache
from .models import CapFeedCountry, CapFeedAlert



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

    updated_countries = cache.get('countryset_country', dict())
    for country_id in updated_countries:
        try:
            country = CapFeedCountry.objects.get(id=country_id)
        except CapFeedCountry.DoesNotExist:
            continue
        calculate_country(country)

    new_updated_countries = cache.get('countryset_country', dict())
    for country_id in updated_countries:
        if updated_countries[country_id] == new_updated_countries[country_id]:
            print(f'finished {CapFeedCountry.objects.get(id=country_id).name}')
            new_updated_countries.pop(country_id)
        else:
            print(f'partly finished {CapFeedCountry.objects.get(id=country_id).name}')

    if len(updated_countries) == 0:
        print(f'finished 0 updates')

    cache.set('countryset_country', new_updated_countries, timeout = None)

def get_country(country_id):
    country_cache_key = "country" + str(country_id)
    return cache.get(country_cache_key, {})
