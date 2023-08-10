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


def initialise_country_cache():
    countries = CapFeedCountry.objects.all()
    for country in countries:
        calculate_country(country)

def get_country(country_id):
    country_cache_key = "country" + str(country_id)
    return cache.get(country_cache_key, {})

def update_country_cache(alert_id):
    alert = CapFeedAlert.objects.get(id = alert_id)
    country = alert.country
    calculate_country(country)