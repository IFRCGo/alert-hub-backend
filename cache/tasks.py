from __future__ import absolute_import, unicode_literals
from celery import shared_task
from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.core.cache import cache
from django.utils import timezone



# Add instruction to update country in cache
@shared_task(bind=True)
def update_cache_instructions(self, country_id):
    updated_countries = cache.get('countryset_country', set())
    updated_countries.add(country_id)
    cache.set('countryset_country', updated_countries, timeout = None)
    updated_countries = cache.get('countryset_admin1', set())
    updated_countries.add(country_id)
    cache.set('countryset_admin1', updated_countries, timeout = None)

    return "Cache update instructions received"

# Update cache
@shared_task(bind=True)
def update_cache(self):
    region_countries_cache.update_region_cache()
    country_admin1s_cache.update_country_cache()
    admin1_alerts_cache.update_admin1_cache()
    info_areas_cache.update_info_cache()

    alerts_cache.update_alerts_cache()
    admin1s_cache.update_admin1s_cache()

    return "Updated cache"
