from django.core.cache import cache
from .models import CapFeedCountry, CapFeedAlert



def initialise_country_cache():
    countries = CapFeedCountry.objects.all()
    for country in countries:
        country_data = {
            'country_id' : country.id,
            'country_name' : country.name,
            'admin1s' : []
            }
        country_alerts = set(country.capfeedalert_set.all().values_list('id', flat=True))
        for admin1 in country.capfeedadmin1_set.all():
            filters = {'urgency': set(), 'severity': set(), 'certainty': set()}
            for alert_admin1 in admin1.capfeedalertadmin1_set.all():
                alert = alert_admin1.alert
                country_alerts.discard(alert.id)
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
        # Compute for alerts that were not matched to any admin1
        filters = {'urgency': set(), 'severity': set(), 'certainty': set()}
        for alert_id in country_alerts:
            alert = CapFeedAlert.objects.get(id=alert_id)
            for info in alert.capfeedalertinfo_set.all():
                filters['urgency'].add(info.urgency)
                filters['severity'].add(info.severity)
                filters['certainty'].add(info.certainty)
        filters['urgency'] = list(filters['urgency'])
        filters['severity'] = list(filters['severity'])
        filters['certainty'] = list(filters['certainty'])
        unknown_admin1_data = {'id': -country.id, 'name': 'Unknown', 'polygon': None, 'multipolygon': None}
        unknown_admin1_data['filters'] = filters
        country_data['admin1s'].append(unknown_admin1_data)
        
        cache.set("country" + str(country.id), country_data, timeout = None)

def get_country(country_id):
    country_cache_key = "country" + str(country_id)
    return cache.get(country_cache_key, {})
