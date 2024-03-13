from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.user.models import User


@shared_task
def send_subscription_email(user_id, subject, template_name, context=None):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return "Invalid User ID"

    context = context or {}
    context.update(
        {
            'user': user,
        }
    )

    message = render_to_string(template_name, context)

    send_mail(
        subject=subject,
        message=strip_tags(message),
        html_message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

    return "Done"


@shared_task
def process_immediate_alerts(subscription_id):
    from .models import SubscriptionAlerts  # Subscription,

    # subscription = Subscription.objects.get(id=subscription_id)
    # subscription_name = subscription.subscription_name
    # user_id = subscription.user_id  # pylint: disable=W0612

    related_alerts = SubscriptionAlerts.objects.filter(subscription=subscription_id, sent=False)

    if not related_alerts:
        return

    # related_alerts_count = related_alerts.count()

    # viewer_link = "https://alert-hub-frontend.azurewebsites.net/account/subscription"

    # context = {  # pylint: disable=W0612
    #     'title': subscription_name,
    #     'count': related_alerts_count,
    #     'viewer_link': viewer_link,
    # }

    # send_subscription_email.delay(user_id, 'New Alerts Matching Your Subscription',
    #                               'subscription_email.html', context)

    related_alerts.update(sent=True)


@shared_task
def process_non_immediate_alerts(sent_flag):
    from .models import Subscription, SubscriptionAlerts

    subscriptions = Subscription.objects.filter(sent_flag=sent_flag)

    for subscription in subscriptions:
        subscription_id = subscription.id
        # subscription_name = subscription.subscription_name
        # user_id = subscription.user_id  # pylint: disable=W0612

        related_alerts = SubscriptionAlerts.objects.filter(subscription=subscription_id, sent=False)

        if not related_alerts:
            continue

        # related_alerts_count = related_alerts.count()

        # viewer_link = "https://alert-hub-frontend.azurewebsites.net/account/subscription"

        # context = {  # pylint: disable=W0612
        #     'title': subscription_name,
        #     'count': related_alerts_count,
        #     'viewer_link': viewer_link,
        # }

        # send_subscription_email.delay(user_id, 'New Alerts Matching Your Subscription',
        #                               'subscription_email.html', context)

        related_alerts.update(sent=True)


@shared_task
def get_incoming_alert(alert_id):
    from .subscription_alert_mapping import map_alert_to_subscription

    return map_alert_to_subscription(alert_id)


@shared_task
def get_removed_alert(alert_id):
    from .subscription_alert_mapping import delete_alert_to_subscription

    return delete_alert_to_subscription(alert_id)


@shared_task
def initialise_task():
    from .subscription_alert_mapping import map_subscriptions_to_alert

    map_subscriptions_to_alert()


@shared_task
def subscription_mapper(subscription_id):
    from apps.subscription.models import Subscription
    from apps.subscription_manager.subscription_alert_mapping import (
        map_subscription_to_alert,
    )

    try:
        map_subscription_to_alert(subscription_id)
    except Subscription.DoesNotExist:
        print(f"Subscription {subscription_id} not exist")
