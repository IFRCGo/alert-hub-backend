from cache import countries_cache, districts_cache, alerts_cache, polygons_cache
from django.http import JsonResponse



def get_countries(request):
    response = countries_cache.get_countries()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_districts_by_country(request, country_id):
    response = districts_cache.get_districts_by_country(country_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alerts_by_district(request, district_id):
    response = alerts_cache.get_alerts_by_district(district_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_polygons_by_info(request, info_id):
    response = polygons_cache.get_polygons_by_info(info_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})
