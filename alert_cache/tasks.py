from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .cache import append_alert_info_to_region_cache, delete_alert_info_from_region_cache

import json
from .models import CapFeedAlert
from django.core.cache import cache

# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id):
    alert_level_result = cache_alerts(alert_id)
    if alert_level_result == "Success":
        cache_alerts_info_into_region_cache(alert_id)
        return f"Alert: {alert_id} is successfully cached."
    elif alert_level_result == "Already Cached":
        return f"Alert: {alert_id} is already cached."
    else:
        return f"Alert: {alert_id} is not cached because it is not in the database."

def cache_alerts_info_into_region_cache(alert_id):
    alert = CapFeedAlert.objects.filter(id=alert_id).first()
    regions_dict = cache.get("regions")
    if alert != None:
        append_alert_info_to_region_cache(regions_dict,alert)
        cache.set("regions", regions_dict, timeout=None)
        cache.set("regions_in_json", json.dumps(regions_dict, indent=None), timeout=None)
def cache_alerts(alert_id):
    #This dictionary stores alerts with all serialised details for fast research
    alert_dictionary = cache.get("alerts")
    if alert_id not in alert_dictionary:
        alert = CapFeedAlert.objects.filter(id=alert_id).first()
        if alert != None:
            alert_dictionary[alert.id] = json.dumps(alert.to_dict())
            cache.set("alerts", alert_dictionary, timeout=None)
            return "Success"
        else:
            return "Failed"
    return "Already Cached"

# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id):
    region_level_result = remove_alerts_info_from_regions_cache(alert_id)
    alert_level_result = remove_alert_from_alert_cache(alert_id)
    return region_level_result + "\n" + alert_level_result


def remove_alerts_info_from_regions_cache(alert_id):
    alert_dict = cache.get("alerts")
    regions_dict = cache.get("regions")
    if alert_id in alert_dict:
        delete_alert_info_from_region_cache(regions_dict,json.loads(alert_dict[alert_id]))
        cache.set("regions", regions_dict, timeout=None)
        cache.set("regions_in_json", json.dumps(regions_dict, indent=None), timeout=None)
        return f"Alert: {alert_id} is removed from regional level records."
    return f"Alert: {alert_id} is not in the cache."

def remove_alert_from_alert_cache(alert_id):
    alert_dictionary = cache.get("alerts")
    if alert_id in alert_dictionary:
        del alert_dictionary[alert_id]
        cache.set("alerts", alert_dictionary, timeout=None)
        return f"Removed alert with id : {alert_id}"
    return f"Alert with id : {alert_id} is not in the cache"