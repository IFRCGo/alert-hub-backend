import json


from django.http import HttpResponse
from cache import region_cache, country_cache,alert_cache


#Get all alerts and show them on page


def get_regions(request):
    return HttpResponse(region_cache.get_regions())

def get_alert_by_id(request, alert_id):
    return HttpResponse(alert_cache.get_alert_by_id(alert_id))

def get_alerts_by_country(request, country_id):
    return HttpResponse(country_cache.get_alerts_by_country(country_id))