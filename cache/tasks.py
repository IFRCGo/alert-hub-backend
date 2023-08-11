from __future__ import absolute_import, unicode_literals
from celery import shared_task
from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.core.cache import cache
from django.utils import timezone



# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id, country_id, admin1_ids, info_ids):
    # Skip if cache has been updated in the last 1 seconds
    # last_cache_update = cache.get("cache_update", None)
    # if last_cache_update and last_cache_update > timezone.now() - timezone.timedelta(seconds = 1):
    #     return "Skipped, cache updated recently"
    
    # # Record cache update time
    # cache.set("cache_update", timezone.now(), timeout = None)
    
    # Update cache
    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache(country_id)
    admin1_alerts_cache.update_admin1_cache(country_id)
    info_areas_cache.update_info_cache(info_ids, True)

    alerts_cache.update_alerts_cache(alert_id, True)

    return "Updated cache for added alert"


# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id, country_id, admin1_ids, info_ids):
    # Skip if cache has been updated in the last 1 seconds
    last_cache_update = cache.get("cache_update", None)
    if last_cache_update and last_cache_update > timezone.now() - timezone.timedelta(seconds = 1):
        return "Skipped, cache updated recently"
    
    # Record cache update time
    cache.set("cache_update", timezone.now(), timeout = None)

    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache(country_id)
    admin1_alerts_cache.update_admin1_cache(country_id)
    info_areas_cache.update_info_cache(info_ids, False)

    alerts_cache.update_alerts_cache(alert_id, False)

    return "Updated cache for removed alert"
