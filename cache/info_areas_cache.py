from django.core.cache import cache
from .models import CapFeedAlertInfo



def calculate_info(info):
    info_data = {
        'info_id' : info.id,
        'areas' : []
    }
    areas = info.capfeedalertinfoarea_set.all()
    for area in areas:
        area_data = area.to_dict()
        area_data['polygons'] = []
        area_data['circles'] = []
        area_data['geocodes'] = []
        polygons = area.capfeedalertinfoareapolygon_set.all()
        for polygon in polygons:
            polygon_data = polygon.to_dict()
            area_data['polygons'].append(polygon_data)
        circles = area.capfeedalertinfoareacircle_set.all()
        for circle in circles:
            circle_data = circle.to_dict()
            area_data['circles'].append(circle_data)
        geocodes = area.capfeedalertinfoareageocode_set.all()
        for geocode in geocodes:
            geocode_data = geocode.to_dict()
            area_data['geocodes'].append(geocode_data)
        info_data['areas'].append(area_data)

    cache.set("info" + str(info.id), info_data, timeout = None)


def initialise_info_cache():
    infos = CapFeedAlertInfo.objects.all()
    for info in infos:
        calculate_info(info)

def get_info(info_id):
    info_cache_key = "info" + str(info_id)
    return cache.get(info_cache_key, {})

def update_info_cache(info_ids, update):
    if update:
        for info_id in info_ids:
            info = CapFeedAlertInfo.objects.get(id=info_id)
            calculate_info(info)
    else:
        for info_id in info_ids:
            info_cache_key = "info" + str(info_id)
            cache.delete(info_cache_key)