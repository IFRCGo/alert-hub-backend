from __future__ import absolute_import, unicode_literals
from celery import shared_task
from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache



# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id, country_id, admin1_ids):
    # Update with initialise method since speed is not an issue
    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache(country_id)
    return "Updated cache for added alert"


# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id, country_id, admin1_ids):
    # Update with initialise method since speed is not an issue
    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache(country_id)
    return "Updated cache for removed alert"
