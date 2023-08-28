from django.core.cache import cache
from .models import CapFeedCountry
from django.utils import timezone



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


def update_admin1_cache():
    print('Updating admin1_alerts cache...')

    update_records = cache.get('update_records', dict())
    cache_records = cache.get('admin1_cache_records', dict())
    old_country_ids = set()
    for country_id in update_records:
        cap_update_time = update_records[country_id]
        cache_update_time = cache_records.get(country_id, None)
        if (cache_update_time is None) or (cache_update_time > cap_update_time):
            try:
                country = CapFeedCountry.objects.get(id=country_id)
                print(f'Updating admin1 cache for {country.name}')
                calculate_country(country)
                cache_records[country_id] = timezone.now()
            except:
                old_country_ids.add(country_id)
    cache.set('admin1_cache_records', cache_records, timeout = None)

    # Remove old country ids
    update_records = cache.get('update_records', dict())
    cache_records = cache.get('admin1_cache_records', dict())
    for old_country_id in old_country_ids:
        update_records.pop(old_country_id)
        cache_records.pop(old_country_id)
    cache.set('update_records', update_records, timeout = None)
    cache.set('admin1_cache_records', cache_records, timeout = None)

def get_admin1(admin1_id):
    admin1_cache_key = "admin1" + str(admin1_id)
    return cache.get(admin1_cache_key, {})
