from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from django.core.cache import cache
import json
from django.utils import timezone
from .models import CapFeedAlert



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

@csrf_exempt
def get_alert_summary(request):
    try:
        post_data = request.POST
        alert_ids = json.loads(post_data['alert_ids'])
        alert_summaries = alerts_cache.get_alert_summary(alert_ids)
        response = json.dumps(alert_summaries)
    except Exception as e:
        error_message = "List of valid alert_ids must be present in http request body. 'alert_ids': []"
        return HttpResponseNotFound(f"Invalid request. {error_message}     {e}")
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False}, safe=False)

def get_alert(request, alert_id):
    response = alerts_cache.get_alert(alert_id)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_alerts(request):
    response = alerts_cache.get_alerts()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

def get_country_feeds(request):
    response = alerts_cache.get_country_feeds()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})
    
def get_country_alerts(request, iso3):
    response = alerts_cache.get_country_alerts(iso3)
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False}, safe=False)

def get_admin1s(request):
    response = admin1s_cache.get_admin1s()
    return JsonResponse(response, json_dumps_params={'indent': 2, 'ensure_ascii': False})

# def clear(request):
#     cache.clear()

#     # Prepare for reinitialisation of cache
#     update_records = dict()
#     for country_id in set(CapFeedAlert.objects.values_list('country', flat=True)):
#         update_records[country_id] = timezone.now()
#     cache.set('update_records', update_records)
#     return HttpResponse("Done")