from django.core.cache import cache
from .models import CapFeedAdmin1



def initialise_admin1_cache():
    admin1s = CapFeedAdmin1.objects.all()
    for admin1 in admin1s:
        admin1_data = {
            'admin1_id' : admin1.id,
            'admin1_name' : admin1.name,
            'alerts' : []
            }
        for alert_admin1 in admin1.capfeedalertadmin1_set.all():
            alert = alert_admin1.alert
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

def get_admin1(admin1_id):
    admin1_cache_key = "admin1" + str(admin1_id)
    return cache.get(admin1_cache_key, {})