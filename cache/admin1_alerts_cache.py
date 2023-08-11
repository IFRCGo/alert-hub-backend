from django.core.cache import cache
from .models import CapFeedAdmin1, CapFeedCountry, CapFeedAlert



def calculate_country(country):
    known_admin1s = []
    for admin1 in country.capfeedadmin1_set.all():
        admin1_data = {
            'admin1_id' : admin1.id,
            'admin1_name' : admin1.name,
            'alerts' : [],
            }
        for alert_admin1 in admin1.capfeedalertadmin1_set.all():
            alert = alert_admin1.alert
            alert_data = alert.to_dict()
            if admin1.id < 0:
                alert_data['admin1_known'] = False
            else:
                alert_data['admin1_known'] = True
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
        if admin1.id < 0:
            unknown_admin1_alerts = admin1_data['alerts']
            cache.set("admin1" + str(admin1.id), admin1_data, timeout = None)
        else:
            known_admin1s.append(admin1_data)
    for known_admin1 in known_admin1s:
        known_admin1['alerts'].extend(unknown_admin1_alerts)
        cache.set("admin1" + str(known_admin1['admin1_id']), known_admin1, timeout = None)


def initialise_admin1_cache():
    countries = CapFeedCountry.objects.all()
    for country in countries:
        calculate_country(country)

def get_admin1(admin1_id):
    admin1_cache_key = "admin1" + str(admin1_id)
    return cache.get(admin1_cache_key, {})

def update_admin1_cache(country_id):
    country = CapFeedCountry.objects.get(id=country_id)
    calculate_country(country)
