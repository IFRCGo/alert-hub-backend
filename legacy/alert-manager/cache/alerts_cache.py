from django.core.cache import cache
from .models import CapFeedAlert, CapFeedFeed



def calculate_country_feeds():
    print('Updating country feeds cache...')
    country_feeds = dict()
    for feed in CapFeedFeed.objects.all():
        iso3 = feed.country.iso3
        if iso3 in country_feeds:
            country_feeds[iso3]['feeds'].append(feed.url)
        else:
            country_feeds[iso3] = {
                'name': feed.country.name,
                'iso3': iso3,
                'feeds': [feed.url]
            }
    cache.set("country_feeds", country_feeds, timeout = None)

def get_country_feeds():
    country_feed_cache_key = "country_feeds"
    return cache.get(country_feed_cache_key, {})
    

def calculate_country_alerts():
    print('Updating country alerts cache...')
    existing_alert_set = cache.get('alertset', set())
    existing_alert_iso3 = cache.get('alertiso3', {})
    alert_set = set(CapFeedAlert.objects.values_list('id', flat=True))
    old_alerts = existing_alert_set.difference(alert_set)
    new_alerts = alert_set.difference(existing_alert_set)
    for old_id in old_alerts:
        iso3 = existing_alert_iso3.get(old_id, None)
        if iso3 is None:
            continue
        cache_key = 'country_alerts' + iso3
        country_alerts = cache.get(cache_key, dict())
        indices_to_remove = []
        for index, alert_data in enumerate(country_alerts):
            if alert_data['id'] == old_id:
                indices_to_remove.append(index)
                cache.delete("alert" + str(old_id))
                cache.delete("alert_summary" + str(old_id))
        for index in indices_to_remove:
            country_alerts.pop(index)
    for new_id in new_alerts:
        try:
            alert = CapFeedAlert.objects.get(id=new_id)
            alert_data = calculate_alert_data(alert, False)
            iso3 = alert.country.iso3
            cache_key = 'country_alerts' + iso3
            country_alerts = cache.get(cache_key, [])
            country_alerts.append(alert_data)
            cache.set(cache_key, country_alerts, timeout = None)
        except CapFeedAlert.DoesNotExist:
            continue
    cache.set('alertset', alert_set, timeout = None)

def get_country_alerts(iso3):
    cache_key = 'country_alerts' + iso3
    return cache.get(cache_key, [])


def update_alerts_cache():
    print('Updating alerts cache...')
    alerts_data = cache.get('alerts', {'alerts': []})
    existing_alert_set = cache.get('alertset2', set())
    alert_set = set(CapFeedAlert.objects.values_list('id', flat=True))
    old_alerts = existing_alert_set.difference(alert_set)
    new_alerts = alert_set.difference(existing_alert_set)
    for old_id in old_alerts:
        for index, alert_data in enumerate(alerts_data['alerts']):
            if alert_data['id'] == old_id:
                alerts_data['alerts'].pop(index)
                cache.delete("alert" + str(old_id))
                cache.delete("alert_summary" + str(old_id))
    for new_id in new_alerts:
        try:
            alert = CapFeedAlert.objects.get(id=new_id)
        except CapFeedAlert.DoesNotExist:
            continue
        alert_data = calculate_alert_data(alert)
        alerts_data['alerts'].append(alert_data)
    cache.set("alerts", alerts_data, timeout = None)
    cache.set('alertset2', alert_set, timeout = None)

def get_alerts():
    alerts_cache_key = "alerts"
    return cache.get(alerts_cache_key, {})


def calculate_alert_data(alert, full = True):
    alert_data = alert.to_dict()
    alert_data['region'] = alert.country.region.name
    alert_data['country'] = alert.country.name
    alert_data['admin1'] = []

    alertadmin1s = alert.capfeedalertadmin1_set.all()
    for alertadmin1 in alertadmin1s:
        alert_data['admin1'].append(alertadmin1.admin1.name)
        
    alert_summary_data = dict()
    alert_summary_data['id'] = alert.id
    alert_summary_data['sent'] = str(alert.sent)
    alert_summary_data['category'] = ''
    alert_summary_data['event'] = ''
    alert_summary_data['admin1'] = alert_data['admin1']
    
    alert_data['info'] = []
    for info in alert.capfeedalertinfo_set.all():
        info_data = info.to_dict()
        if alert_summary_data['category'] == '':
            alert_summary_data['category'] = info_data['category']
        if alert_summary_data['event'] == '':
            alert_summary_data['event'] = info_data['event']
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
    cache.set("alert_summary" + str(alert.id), alert_summary_data, timeout = None)
    
    alert_data['info'] = []
    for info in alert.capfeedalertinfo_set.all():
        info_data = {'category': info.category, 'event': info.event}
        alert_data['info'].append(info_data)
    
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

    if full:
        return alert_data
    else:
        alert_data.pop('url', None)
        alert_data.pop('sender', None)
        alert_data.pop('sent', None)
        alert_data.pop('identifier', None)
        alert_data.pop('region', None)
        alert_data.pop('source', None)
        alert_data.pop('region', None)
        alert_data.pop('country', None)
        alert_data.pop('admin1', None)
        alert_data.pop('region', None)
        return alert_data


def get_alert_summary(alert_ids):
    summaries = []
    for alert_id in alert_ids:
        alert_cache_key = "alert_summary" + str(alert_id)
        summaries.append(cache.get(alert_cache_key, {}))
    return summaries

def get_alert(alert_id):
    alert_cache_key = "alert" + str(alert_id)
    return cache.get(alert_cache_key, {})
