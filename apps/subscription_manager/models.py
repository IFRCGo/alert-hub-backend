# These files are used for storing required models of subscriptions and their correlated alerts
from django.db import models
from apps.subscription.models import Subscription


class Alert(models.Model):
    id = models.IntegerField(primary_key=True)
    subscriptions = models.ManyToManyField(Subscription, through="SubscriptionAlerts")


class SubscriptionAlerts(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    sent = models.BooleanField(default=False)
