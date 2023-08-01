import json

from . import cache
from django.http import HttpResponse

#Get all alerts and show them on page


def get_regions(request):
    return HttpResponse(cache.get_regions())

def get_alert_by_id(request, alert_id):
    return HttpResponse(cache.get_alert_by_id(alert_id))

def get_region_by_id(request, region_id):
    return