from apps.cap_feed.factories import (
    Admin1Factory,
    AlertFactory,
    AlertInfoFactory,
    CountryFactory,
    FeedFactory,
    RegionFactory,
)
from apps.cap_feed.models import Alert, AlertInfo
from apps.subscription.factories import UserAlertSubscriptionFactory
from apps.subscription.models import SubscriptionAlert
from apps.subscription.tasks import process_pending_subscription_alerts
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestSubscriptionMutation(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

        self.r_asia = RegionFactory.create(name="Asia")
        self.c_nepal = CountryFactory.create(region=self.r_asia)
        self.ad_bagmati = Admin1Factory.create(country=self.c_nepal)

    def test_subscription_alert_tagging(self):
        feed1 = FeedFactory.create(country=self.c_nepal)
        alert1 = AlertFactory.create(
            feed=feed1,
            country=self.c_nepal,
            admin1s=[self.ad_bagmati],
            # is_processed_by_subscription=True,
        )
        AlertInfoFactory.create(
            alert=alert1,
            category=AlertInfo.Category.HEALTH,
            urgency=AlertInfo.Urgency.IMMEDIATE,
            severity=AlertInfo.Severity.EXTREME,
            certainty=AlertInfo.Certainty.OBSERVED,
        )

        UserAlertSubscriptionFactory.create(
            user=self.user,
            filter_alert_country=self.c_nepal,
            filter_alert_admin1s=[self.ad_bagmati.id],
            filter_alert_urgencies=[AlertInfo.Urgency.IMMEDIATE],
            filter_alert_severities=[],
            filter_alert_certainties=[],
            filter_alert_categories=[],
        )

        assert Alert.objects.filter(is_processed_by_subscription=False).count() == 1
        assert SubscriptionAlert.objects.count() == 0
        process_pending_subscription_alerts()
        assert Alert.objects.filter(is_processed_by_subscription=False).count() == 0
        assert SubscriptionAlert.objects.count() != 0
