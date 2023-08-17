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


def update_info_cache():
    print('Updating info_areas cache...')
    
    existing_info_set = cache.get('infoset', set())
    info_set = set(CapFeedAlertInfo.objects.all().values_list('id', flat=True))
    old_infos = existing_info_set.difference(info_set)
    new_infos = info_set.difference(existing_info_set)
    for old_id in old_infos:
        cache.delete("info" + str(old_id))
    for new_id in new_infos:
        try:
            info = CapFeedAlertInfo.objects.get(id=new_id)
        except CapFeedAlertInfo.DoesNotExist:
            continue
        calculate_info(info)
    cache.set('infoset', info_set, timeout = None)

def get_info(info_id):
    info_cache_key = "info" + str(info_id)
    return cache.get(info_cache_key, {})
