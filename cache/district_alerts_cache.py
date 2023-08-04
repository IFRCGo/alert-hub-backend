from django.core.cache import cache
from .models import CapFeedDistrict



def initialise_district_cache():
    districts = CapFeedDistrict.objects.all()
    for district in districts:
        district_data = {
            'district_id' : district.id,
            'district_name' : district.name,
            'alerts' : []
            }
        for alert_district in district.capfeedalertdistrict_set.all():
            alert = alert_district.alert
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
            district_data['alerts'].append(alert_data)
            
        cache.set("district" + str(district.id), district_data, timeout = None)

def get_district(district_id):
    district_cache_key = "district" + str(district_id)
    return cache.get(district_cache_key, {})