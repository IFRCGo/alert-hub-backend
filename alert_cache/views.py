import json

from .cache import get_alert
from django.http import HttpResponse

#Get all alerts and show them on page
def get_alerts(request):
    return HttpResponse(get_alert())