from django.core.cache import cache
from .models import CapFeedDistrict



def initialise_alerts_cache():
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
            district_data['alerts'].append(alert_data)
            for alert_info in alert.capfeedalertinfo_set.all():
                info = alert_info.to_dict()
                alert_data['info'].append(info)
        cache.set("district" + str(district.id), district_data, timeout = None)

def get_alerts_by_district(district_id):
    district_cache_key = "district" + str(district_id)
    return cache.get(district_cache_key, {})