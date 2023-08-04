from __future__ import absolute_import, unicode_literals
from celery import shared_task



# Add the incoming alerts in cache
@shared_task(bind=True)
def cache_incoming_alert(self, alert_id):
    # alert_level_result = cache_incoming_alerts(alert_id)
    # if alert_level_result == "Success":
    #     cache_incoming_alerts_info_into_region_cache(alert_id)
    #     return f"Alert: {alert_id} is successfully cached."
    # elif alert_level_result == "Already Cached":
    #     return f"Alert: {alert_id} is already cached."
    # else:
    #     return f"Alert: {alert_id} is not cached because it is not in the database."
    return "Not implemented yet"


# Delete the removed alerts in cache
@shared_task(bind=True)
def remove_cached_alert(self, alert_id):
    # region_level_result = remove_alerts_info_from_regions_cache(alert_id)
    # alert_level_result = remove_alert_from_alert_cache(alert_id)
    # return region_level_result + "\n" + alert_level_result
    return "Not implemented yet"

