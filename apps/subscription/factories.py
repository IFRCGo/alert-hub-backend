import factory
from factory.django import DjangoModelFactory

from .models import UserAlertSubscription


class UserAlertSubscriptionFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'Subscription-{n}')
    filter_alert_admin1s = []
    filter_alert_urgencies = []
    filter_alert_severities = []
    filter_alert_certainties = []
    filter_alert_categories = []

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = UserAlertSubscription
