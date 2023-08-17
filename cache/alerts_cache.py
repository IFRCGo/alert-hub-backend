from django.core.cache import cache
from .models import CapFeedAlert



def calculate_alert(alert):
    alert_data = alert.to_dict()
    alert_data['region'] = alert.country.region.name
    alert_data['country'] = alert.country.name
    alert_data['admin1'] = []
    alertadmin1s = alert.capfeedalertadmin1_set.all()
    for alertadmin1 in alertadmin1s:
        alert_data['admin1'].append(alertadmin1.admin1.name)
    alert_data['info'] = []
    for info in alert.capfeedalertinfo_set.all():
        info_data = info.to_dict()
        info_data['parameter'] = []
        parameters = info.capfeedalertinfoparameter_set.all()
        for parameter in parameters:
            parameter_data = parameter.to_dict()
            info_data['parameter'].append(parameter_data)
        info_data['area'] = []
        areas = info.capfeedalertinfoarea_set.all()
        for area in areas:
            area_data = area.to_dict()
            area_data['polygon'] = []
            for polygon in area.capfeedalertinfoareapolygon_set.all():
                polygon_data = polygon.to_dict()
                area_data['polygon'].append(polygon_data)
            area_data['circle'] = []
            for circle in area.capfeedalertinfoareacircle_set.all():
                circle_data = circle.to_dict()
                area_data['circle'].append(circle_data)
            area_data['geocode'] = []
            for geocode in area.capfeedalertinfoareageocode_set.all():
                geocode_data = geocode.to_dict()
                area_data['geocode'].append(geocode_data)
            info_data['area'].append(area_data)
        alert_data['info'].append(info_data)

    cache.set("alert" + str(alert.id), alert_data, timeout = None)
    
    alert_data['info'] = []
    for info in alert.capfeedalertinfo_set.all():
        info_data = {'category': info.category, 'event': info.event}
        alert_data['info'].append(info_data)
    return alert_data

def update_alerts_cache():
    print('Updating alerts cache...')
    alerts_data = cache.get('alerts', {'alerts': []})
    existing_alert_set = cache.get('alertset', set())
    alert_set = set(CapFeedAlert.objects.all().values_list('id', flat=True))
    old_alerts = existing_alert_set.difference(alert_set)
    new_alerts = alert_set.difference(existing_alert_set)
    for old_id in old_alerts:
        for index, alert_data in enumerate(alerts_data['alerts']):
            if alert_data['id'] == old_id:
                alerts_data['alerts'].pop(index)
                cache.delete("alert" + str(old_id))
    for new_id in new_alerts:
        try:
            alert = CapFeedAlert.objects.get(id=new_id)
        except CapFeedAlert.DoesNotExist:
            continue
        alert_data = calculate_alert(alert)
        alert_data.pop('scope', None)
        alert_data.pop('code', None)
        alert_data.pop('note', None)
        alert_data.pop('status', None)
        alert_data.pop('msg_type', None)
        alert_data.pop('references', None)
        alert_data.pop('incidents', None)
        alert_data.pop('restriction', None)
        alert_data.pop('addresses', None)
        alert_data['region'] = alert.country.region.name
        alert_data['country'] = alert.country.name
        alert_data['admin1'] = []
        alertadmin1s = alert.capfeedalertadmin1_set.all()
        for alertadmin1 in alertadmin1s:
            alert_data['admin1'].append(alertadmin1.admin1.name)
        alerts_data['alerts'].append(alert_data)
    cache.set("alerts", alerts_data, timeout = None)
    cache.set('alertset', alert_set, timeout = None)

def get_alert(alert_id):
    alert_cache_key = "alert" + str(alert_id)
    return cache.get(alert_cache_key, {})

def get_alerts():
    alerts_cache_key = "alerts"
    return cache.get(alerts_cache_key, {})
