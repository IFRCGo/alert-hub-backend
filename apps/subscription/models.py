from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext

from apps.cap_feed.models import Alert, AlertInfo, Country
from apps.user.models import User


class UserAlertSubscription(models.Model):
    LIMIT_PER_USER = 10

    class EmailFrequency(models.IntegerChoices):
        DAILY = 1, gettext("Daily")
        WEEKLY = 2, gettext("Weekly")
        MONTHLY = 3, gettext("Monthly")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    # TODO: Keep change history?
    # Filters
    filter_alert_country = models.ForeignKey(Country, on_delete=models.PROTECT)
    filter_alert_admin1s = ArrayField(models.BigIntegerField(), blank=True, default=list)
    filter_alert_urgencies = ArrayField(models.CharField(choices=AlertInfo.Urgency.choices), blank=True, default=list)
    filter_alert_severities = ArrayField(models.CharField(choices=AlertInfo.Severity.choices), blank=True, default=list)
    filter_alert_certainties = ArrayField(models.CharField(choices=AlertInfo.Certainty.choices), blank=True, default=list)
    filter_alert_categories = ArrayField(models.CharField(choices=AlertInfo.Category.choices), blank=True, default=list)

    # Notification config
    notify_by_email = models.BooleanField(default=False)
    email_frequency = models.PositiveSmallIntegerField(choices=EmailFrequency.choices, default=EmailFrequency.WEEKLY)
    email_last_sent_at = models.DateTimeField(null=True, blank=True)

    alerts = models.ManyToManyField(
        Alert,
        blank=True,
        through="SubscriptionAlert",
        related_name="subscriptions",
    )

    filter_alert_country_id: int


class SubscriptionAlert(models.Model):
    subscription = models.ForeignKey(UserAlertSubscription, on_delete=models.CASCADE, related_name="+")
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="+")
