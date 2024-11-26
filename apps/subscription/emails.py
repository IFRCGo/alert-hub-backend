from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.subscription.models import SubscriptionAlert, UserAlertSubscription
from apps.user.models import EmailNotificationType, User
from main.permalinks import Permalink
from main.tokens import TokenManager
from utils.emails import send_email


def generate_unsubscribe_user_alert_subscription_url(subscription: UserAlertSubscription) -> str:
    uid = urlsafe_base64_encode(force_bytes(subscription.pk))
    # TODO: Fix typing
    token = TokenManager.user_subscription_unsubscribe_generator.make_token(subscription)  # type: ignore[reportArgumentType]
    return Permalink.unsubscribe_user_alert_subscription(uid, token)


def generate_user_alert_subscription_email_context(
    user: User,
    email_frequency: UserAlertSubscription.EmailFrequency,
) -> tuple[dict, models.QuerySet[UserAlertSubscription]]:
    # NOTE: Number of subscription is static and less than UserAlertSubscription.LIMIT_PER_USER
    subscription_qs = UserAlertSubscription.objects.filter(user=user, email_frequency=email_frequency)

    if email_frequency == UserAlertSubscription.EmailFrequency.DAILY:
        from_datetime_threshold = timezone.now() - timedelta(hours=24)
    elif email_frequency == UserAlertSubscription.EmailFrequency.WEEKLY:
        from_datetime_threshold = timezone.now() - timedelta(days=7)
    elif email_frequency == UserAlertSubscription.EmailFrequency.MONTHLY:
        # TODO: Calculate days instead of using 30 days
        from_datetime_threshold = timezone.now() - timedelta(days=30)

    subscription_data = [
        {
            'subscription': subscription,
            'unsubscribe_url': generate_unsubscribe_user_alert_subscription_url(subscription),
            'latest_alerts': [
                subscription_alert.alert
                # NOTE: N+1 query, but N < 10 for now
                # TODO: Index/partition alert__sent column?
                for subscription_alert in (
                    SubscriptionAlert.objects.select_related('alert')
                    .filter(
                        subscription=subscription,
                        alert__sent__gte=from_datetime_threshold,
                    )
                    .order_by('-alert__sent')[:5]
                )
            ],
        }
        for subscription in subscription_qs
    ]

    context = {
        'subscriptions': subscription_data,
    }

    return context, subscription_qs


def send_user_alert_subscription_email(user: User, email_frequency: UserAlertSubscription.EmailFrequency):
    context, subscription_qs = generate_user_alert_subscription_email_context(user, email_frequency)
    sent_at = timezone.now()

    send_email(
        user=user,
        email_type=EmailNotificationType.ALERT_SUBSCRIPTIONS,
        subject="Daily Alerts",  # TODO: Is this fine?
        email_html_template='emails/subscription/body.html',
        email_text_template='emails/subscription/body.txt',
        context=context,
    )

    # Post action
    subscription_qs.update(email_last_sent_at=sent_at)


def send_user_alert_subscriptions_email(email_frequency: UserAlertSubscription.EmailFrequency):
    # TODO: Send in parallel if email service supports it
    users_qs = User.objects.filter(
        id__in=UserAlertSubscription.objects.filter(email_frequency=email_frequency).values('user'),
    )

    # TODO: Handle failure
    for user in users_qs.iterator():
        # TODO: Trigger this as cronjob
        # TODO: Pass timezone.now for ref time
        send_user_alert_subscription_email(user, email_frequency)
