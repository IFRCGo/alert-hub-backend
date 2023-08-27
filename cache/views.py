from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.template import loader
from django.core.cache import cache
from django.utils import timezone



def index(request):
    context = {}
    template = loader.get_template("cache/index.html")
    return HttpResponse(template.render(context, request))

def get_region(request, region_id):
    response = region_countries_cache.get_region(region_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_regions(request):
    response = region_countries_cache.get_regions()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_country(request, country_id):
    response = country_admin1s_cache.get_country(country_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_admin1(request, admin1_id):
    try:
        admin1_id = int(admin1_id)
    except ValueError:
        return HttpResponseNotFound("Invalid admin1_id")
    response = admin1_alerts_cache.get_admin1(admin1_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_info(request, info_id):
    response = info_areas_cache.get_info(info_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alert_summary(request, alert_id):
    response = alerts_cache.get_alert_summary(alert_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alert(request, alert_id):
    response = alerts_cache.get_alert(alert_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alerts(request):
    response = alerts_cache.get_alerts()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_admin1s(request):
    response = admin1s_cache.get_admin1s()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def clear(request):
    cache.clear
    return HttpResponse("Done")