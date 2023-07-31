import json

from . import cache
from django.http import HttpResponse

#Get all alerts and show them on page
def get_alerts(request):
    return HttpResponse(cache.get_alerts())

def get_countries(request):
    return HttpResponse(cache.get_countries())

def get_alert_by_id(request, alert_id):
    return HttpResponse(cache.get_alert_by_id(alert_id))
def get_country_by_id(request, country_id):
    return HttpResponse(cache.get_country_by_id(country_id))