from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.template import loader
from django.core.cache import cache



def index(request):
    context = {}
    template = loader.get_template("cache/index.html")
    return HttpResponse(template.render(context, request))

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

def get_alert(request, alert_id):
    response = alerts_cache.get_alert(alert_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alerts(request):
    response = alerts_cache.get_alerts()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_admin1s(request):
    response = admin1s_cache.get_admin1s()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def refresh_cache(request):
    cache.clear()
    print('Initialising region_countries cache...')
    region_countries_cache.initialise_region_cache()
    print(len(cache.keys('*')))
    print('Initialising country_admin1s cache...')
    country_admin1s_cache.initialise_country_cache()
    print(len(cache.keys('*')))
    print('Initialising admin1_alerts cache...')
    admin1_alerts_cache.initialise_admin1_cache()
    print(len(cache.keys('*')))
    print('Initialising info_areas cache...')
    info_areas_cache.initialise_info_cache()
    print(len(cache.keys('*')))
    print('Initialising alerts cache...')
    alerts_cache.initialise_alerts_cache()
    print(len(cache.keys('*')))
    print('Initialising admin1s cache...')
    admin1s_cache.initialise_admin1s_cache()
    print(len(cache.keys('*')))
    response = {'status': 'success'}
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def clear_cache(request):
    cache.clear()
    response = {'status': 'success'}
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})