from __future__ import absolute_import, unicode_literals
from celery import shared_task

import json
from .models import CapFeedAlert
from django.core.cache import cache

# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id):
    #This dictionary stores all alerts in short format
    short_alerts_dictionary = cache.get("short_alert_dictionary")
    #This dictionary stores alerts with all serialised details for fast research
    alert_dictionary = cache.get("alert_dictionary")
    number = cache.get("number")
    if alert_id not in short_alerts_dictionary:
        alert = CapFeedAlert.objects.filter(id=alert_id).first()
        if alert != None:
            short_alerts_dictionary[alert_id] = alert.to_dict_in_short()
            alert_dictionary[alert.id] = json.dumps(alert.to_dict())
            cache.set("short_alert_dictionary", short_alerts_dictionary, timeout=None)
            cache.set("alert_dictionary", alert_dictionary, timeout=None)
            cache.set("alerts_in_json", json.dumps(list(short_alerts_dictionary.values()), indent=None),
                      timeout=None)
            return f"Cached alert with id : {alert_id}"
        else:
            return f"Alert: {alert_id} is not found in database"
    return f"Alert: {alert_id} is already cached"

# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id):
    short_alert_dictionary = cache.get("short_alert_dictionary")
    alert_dictionary = cache.get("alert_dictionary")
    if alert_id in short_alert_dictionary:
        del short_alert_dictionary[alert_id]
        del alert_dictionary[alert_id]
        cache.set("short_alert_dictionary", short_alert_dictionary, timeout=None)
        cache.set("alert_dictionary", alert_dictionary, timeout=None)
        cache.set("alerts_in_json", json.dumps(list(short_alert_dictionary.values()), indent=None),
                  timeout=None)
        return f"Removed alert with id : {alert_id}"
    return f"Alert with id : {alert_id} is not in the cache"