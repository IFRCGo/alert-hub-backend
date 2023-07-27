from __future__ import absolute_import, unicode_literals
from celery import shared_task

import json
from .models import CapFeedAlert
from django.core.cache import cache

# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id):
    alerts_dictionary = cache.get("alerts")
    if alert_id not in alerts_dictionary.keys():
        alert = CapFeedAlert.objects.filter(id=alert_id).first()
        if alert != None:
            alerts_dictionary = cache.get("alerts")
            alerts_dictionary[alert_id] = alert.to_dict()
            cache.set("alerts", alerts_dictionary, timeout=None)
            cache.set("alerts_in_json", json.dumps(alerts_dictionary, indent=None), timeout=None)
            return f"Cached alert with id : {alert_id}"
        else:
            return f"Alert: {alert_id} is not found in database"
    return f"Alert: {alert_id} is already cached"

# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id):
    alerts_dictionary = cache.get("alerts")
    if alert_id in alerts_dictionary.keys():
        del alerts_dictionary[alert_id]
        cache.set("alerts", alerts_dictionary, timeout=None)
        cache.set("alerts_in_json", json.dumps(alerts_dictionary, indent=None), timeout=None)
        return f"Removed alert with id : {alert_id}"
    return f"Alert with id : {alert_id} is not in the cache"