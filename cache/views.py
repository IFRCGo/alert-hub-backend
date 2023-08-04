from cache import country_districts_cache, district_alerts_cache, info_areas_cache, region_countries_cache
from django.http import JsonResponse



def get_regions(request):
    response = region_countries_cache.get_regions()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_country(request, country_id):
    response = country_districts_cache.get_country(country_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_district(request, district_id):
    response = district_alerts_cache.get_district(district_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_info(request, info_id):
    response = info_areas_cache.get_info(info_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})
