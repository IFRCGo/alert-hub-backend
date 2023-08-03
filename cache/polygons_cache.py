from django.core.cache import cache
from .models import CapFeedAlertInfo



def initialise_polygons_cache():
    infos = CapFeedAlertInfo.objects.all()
    for info in infos:
        info_data = {}
        info_data['id'] = info.id
        info_data['areas'] = []
        areas = info.capfeedalertinfoarea_set.all()
        for area in areas:
            area_data = area.to_dict()
            area_data['polygons'] = []
            polygons = area.capfeedalertinfoareapolygon_set.all()
            for polygon in polygons:
                polygon_data = polygon.to_dict()
                area_data['polygons'].append(polygon_data)
        info_data['areas'].append(area_data)

        cache.set("info" + str(info.id), info_data, timeout = None)

def get_polygons_by_info(info_id):
    info_cache_key = "info" + str(info_id)
    return cache.get(info_cache_key, {})