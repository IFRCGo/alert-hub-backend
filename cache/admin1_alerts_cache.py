from django.core.cache import cache
from .models import CapFeedAdmin1, CapFeedCountry, CapFeedAlert



def initialise_admin1_cache():
    countries = CapFeedCountry.objects.all()
    admin1s = CapFeedAdmin1.objects.all()
    for country in countries:
        country_alerts = set(country.capfeedalert_set.all().values_list('id', flat=True))
        for admin1 in country.capfeedadmin1_set.all():
            admin1_data = {
                'admin1_id' : admin1.id,
                'admin1_name' : admin1.name,
                'alerts' : []
                }
            for alert_admin1 in admin1.capfeedalertadmin1_set.all():
                alert = alert_admin1.alert
                country_alerts.discard(alert.id)
                alert_data = alert.to_dict()
                alert_data['info'] = []
                for info in alert.capfeedalertinfo_set.all():
                    info_data = info.to_dict()
                    info_data['parameter'] = []
                    parameters = info.capfeedalertinfoparameter_set.all()
                    for parameter in parameters:
                        parameter_data = parameter.to_dict()
                        info_data['parameter'].append(parameter_data)
                    alert_data['info'].append(info_data)
                admin1_data['alerts'].append(alert_data)
                
            cache.set("admin1" + str(admin1.id), admin1_data, timeout = None)
            
        # Compute for alerts that were not matched to any admin1
        if len(country_alerts) > 0:
            admin1_data = {
                'admin1_id' : -country.id,
                'admin1_name' : 'Unknown',
                'alerts' : []
                }
            for alert_id in country_alerts:
                alert = CapFeedAlert.objects.get(id=alert_id)
                alert_data = alert.to_dict()
                alert_data['info'] = []
                for info in alert.capfeedalertinfo_set.all():
                    info_data = info.to_dict()
                    info_data['parameter'] = []
                    parameters = info.capfeedalertinfoparameter_set.all()
                    for parameter in parameters:
                        parameter_data = parameter.to_dict()
                        info_data['parameter'].append(parameter_data)
                    alert_data['info'].append(info_data)
                admin1_data['alerts'].append(alert_data)
                
            cache.set("admin1" + str(-country.id), admin1_data, timeout = None)

def get_admin1(admin1_id):
    admin1_cache_key = "admin1" + str(admin1_id)
    return cache.get(admin1_cache_key, {})