from __future__ import absolute_import, unicode_literals
from celery import shared_task
from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.core.cache import cache
from django.utils import timezone



# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id, country_id, admin1_ids, info_ids):
    updated_countries = cache.get('countryset_country', set())
    updated_countries.add(country_id)
    cache.set('countryset_country', updated_countries, timeout = None)
    updated_countries = cache.get('countryset_admin1', set())
    updated_countries.add(country_id)
    cache.set('countryset_admin1', updated_countries, timeout = None)

    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache()
    admin1_alerts_cache.update_admin1_cache()
    info_areas_cache.update_info_cache()

    alerts_cache.update_alerts_cache()

    return "Updated cache for added alert"


# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id, country_id, admin1_ids, info_ids):
    updated_countries = cache.get('countryset_country', set())
    updated_countries.add(country_id)
    cache.set('countryset_country', updated_countries, timeout = None)
    updated_countries = cache.get('countryset_admin1', set())
    updated_countries.add(country_id)
    cache.set('countryset_admin1', updated_countries, timeout = None)

    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache()
    admin1_alerts_cache.update_admin1_cache()
    info_areas_cache.update_info_cache()

    alerts_cache.update_alerts_cache()

    return "Updated cache for removed alert"
