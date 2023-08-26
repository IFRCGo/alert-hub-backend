import json

from django.http import HttpResponse
from django.core.cache import cache
from subscription_dir.models import Subscription
from .subscription_alert_mapping import get_subscription_alerts_without_mapping_records
def get_subscirption_alerts(request, subscription_id):
    try:
        # Try to acquire the lock without waiting. If there is a lock, it means susbcription is
        # still mapping the alerts.
        lock_acquired = cache.keys("*")
        if str(subscription_id) in lock_acquired:
            return HttpResponse("Subscription is still matching alerts!", status=404)

        subscription = Subscription.objects.get(id=subscription_id)
    except Subscription.DoesNotExist:
        return HttpResponse("Subscription is not found!", status=404)

    alert_list = subscription.get_alert_id_list()
    if len(alert_list) == 0:
        return HttpResponse("There is no alerts!", status=404)

    result = json.dumps(alert_list)
    return HttpResponse(result)


def get_subscription_alerts_in_real_time(request, subscription_id):
    result = get_subscription_alerts_without_mapping_records(subscription_id)
    if not result:
        return HttpResponse("Subscription is not found!", status=404)
    return HttpResponse(result)
