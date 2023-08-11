import json

from .external_alert_models import CapFeedAlert, CapFeedAdmin1
from subscription_dir.models import Subscription
from .models import *


def map_subscriptions_to_alert():
    for subscription in Subscription.objects.all():
        map_subscription_to_alert(subscription)


def map_subscription_to_alert(subscription):
    for id in subscription.district_ids:
        admin1 = CapFeedAdmin1.objects.filter(id=id).first()
        if admin1 == None:
            continue
        potential_alert_set = admin1.capfeedalert_set.all()

        for alert in potential_alert_set:
            first_info = alert.capfeedalertinfo_set.first()
            if first_info.severity in subscription.severity_array and \
                    first_info.certainty in subscription.certainty_array and \
                    first_info.urgency in subscription.urgency_array:
                internal_alert = Alert.objects.filter(id=alert.id).first()
                if internal_alert is None:
                    internal_alert = Alert.objects.create(id=alert.id, serialised_string=json.dumps(
                        alert.to_dict()))
                    internal_alert.save()
                internal_alert.subscriptions.add(subscription)

def map_alert_to_subscription(alert_id):
    alert = CapFeedAlert.objects.filter(id=alert_id).first()
    converted_alert = Alert.objects.filter(id=alert_id).first()
    if alert == None:
        return f"Alert with id {alert_id} is not existed"
    if converted_alert != None:
        return f"Alert with id {alert_id} is already converted and matched subscription"
    alert_admin1_ids = []
    for admin1 in alert.admin1s.all():
        alert_admin1_ids.append(admin1.id)
    subscriptions = Subscription.objects.filter(district_ids__overlap=alert_admin1_ids)

    first_info = alert.capfeedalertinfo_set.first()
    updated_subscription_ids = []
    for subscription in subscriptions:
        if first_info.severity in subscription.severity_array and \
                first_info.certainty in subscription.certainty_array and \
                first_info.urgency in subscription.urgency_array:
            internal_alert = Alert.objects.create(id=alert.id, serialised_string=json.dumps(
                    alert.to_dict()))
            internal_alert.save()
            internal_alert.subscriptions.add(subscription)
            #Still need to update cache
            updated_subscription_ids.append(subscription.id)
    return updated_subscription_ids




def print_all_admin1s_in_country(id):
    ids = []
    admin1s = CapFeedAdmin1.objects.filter(country__id=id)
    for admin in admin1s:
        ids.append(admin.id)
