import json

from .models import CapFeedAlert
from django.core.cache import cache


#Alert Level Cache
def initialise_alert_cache():
    all_alerts = CapFeedAlert.objects.all()

    for alert in all_alerts:
        cache.set("alert"+str(alert.id), json.dumps(alert.to_dict(), indent=None), timeout=None)

def cache_incoming_alerts(alert_id):
    cache_keys = cache.client.keys('*')
    alert_cache_key = "alert" + str(alert_id)

    if alert_cache_key not in cache_keys:
        alert = CapFeedAlert.objects.filter(id=alert_id).first()
        if alert != None:
            cache.set(alert_cache_key, json.dumps(alert.to_dict(),indent=None), timeout=None)
            return "Success"
        else:
            return "Failed"
    return "Already Cached"

def remove_alert_from_alert_cache(alert_id):
    cache_keys = cache.client.keys('*')
    alert_cache_key = "alert" + str(alert_id)

    if alert_cache_key in cache_keys:
        cache.delete(alert_cache_key)
        return f"Removed alert with id : {alert_id}"
    return f"Alert with id : {alert_id} is not in the cache"

def get_alert_by_id(alert_id):
    cache_keys = cache.client.keys('*')
    alert_cache_key = "alert" + str(alert_id)

    if alert_cache_key in cache_keys:
        return cache.get(alert_cache_key)
    else:
        return f"Alert {alert_id} is not found!"