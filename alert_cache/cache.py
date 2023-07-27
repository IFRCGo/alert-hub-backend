import json

from .models import CapFeedAlert
from django.core.cache import cache

def cache_alert():
    all_alerts = CapFeedAlert.objects.all()
    alert_dictionary = {}
    for alert in all_alerts:
        alert_dictionary[alert.id] = json.dumps(alert.to_dict())
    cache.set("alerts",alert_dictionary,timeout=None)
    print(len(alert_dictionary))

def get_alert():
    alerts = cache.get("alerts")
    print(len(alerts))
    return alerts