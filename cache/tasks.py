from __future__ import absolute_import, unicode_literals
from celery import shared_task
from cache import admin1_alerts_cache, country_admin1s_cache, info_areas_cache, region_countries_cache, alerts_cache, admin1s_cache
from django.core.cache import cache
from django.utils import timezone



# Add instruction to update country in cache
@shared_task(bind=True)
def update_cache_instructions(self, country_id):
    update_records = cache.get('update_records', dict())
    update_records[country_id] = timezone.now()
    cache.set('update_records', update_records, timeout = None)

    return "Cache update instructions received"

# Update non-priority cache part 1
@shared_task(bind=True)
def update_cache_1(self):
    print('Updating cache part 1')
    country_admin1s_cache.update_country_cache()
    admin1_alerts_cache.update_admin1_cache()

    return "Updated cache part 1"

# Update non-priority cache part 2
@shared_task(bind=True)
def update_cache_2(self):
    print('Updating cache part 2')
    region_countries_cache.update_region_cache()
    info_areas_cache.update_info_cache()
    admin1s_cache.update_admin1s_cache()

    return "Updated cache part 2"

# Update priority cache
@shared_task(bind=True)
def update_cache_fast(self):
    alerts_cache.calculate_country_feeds()
    alerts_cache.calculate_country_alerts()

    return "Updated external alerts api cache"