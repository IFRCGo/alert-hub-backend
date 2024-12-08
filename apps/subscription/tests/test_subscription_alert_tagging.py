from collections import defaultdict

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
from apps.subscription.models import SubscriptionAlert, UserAlertSubscription
from apps.subscription.tasks import process_pending_subscription_alerts
from apps.user.factories import UserFactory
from main.tests import TestCase

Category = AlertInfo.Category
Urgency = AlertInfo.Urgency
Severity = AlertInfo.Severity
Certainty = AlertInfo.Certainty


class TestSubscriptionMutation(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

        self.r_asia = RegionFactory.create(name="Asia")
        self.c_nepal = CountryFactory.create(region=self.r_asia)
        self.ad_bagmati = Admin1Factory.create(country=self.c_nepal)
        self.ad_lalitpur = Admin1Factory.create(country=self.c_nepal)
        self.ad_bhaktapur = Admin1Factory.create(country=self.c_nepal)

    def test_subscription_alert_tagging(self):
        feed1 = FeedFactory.create(country=self.c_nepal)

        # Alerts
        alert1, alert2, alert3, alert4 = all_alerts = [
            AlertFactory.create(
                feed=_data[0],
                country=_data[1],
                admin1s=_data[2],
            )
            for _data in [
                (feed1, self.c_nepal, [self.ad_bagmati]),  # 1
                (feed1, self.c_nepal, [self.ad_lalitpur]),  # 2
                (feed1, self.c_nepal, [self.ad_bhaktapur]),  # 3
                (feed1, self.c_nepal, [self.ad_bagmati, self.ad_bhaktapur]),  # 4
            ]
        ]

        # Processed alerts (Noise data)
        AlertFactory.create_batch(
            9,
            feed=feed1,
            country=self.c_nepal,
            admin1s=[],
            is_processed_by_subscription=True,
        )

        # AlertInfos
        alert_info_dataset = [
            (alert1, ((Category.HEALTH, Urgency.IMMEDIATE, Severity.EXTREME, Certainty.OBSERVED),)),
            (
                alert2,
                (
                    (Category.HEALTH, Urgency.IMMEDIATE, Severity.EXTREME, Certainty.OBSERVED),
                    (Category.HEALTH, Urgency.FUTURE, Severity.MODERATE, Certainty.OBSERVED),
                ),
            ),
            (alert3, ((Category.HEALTH, Urgency.FUTURE, Severity.MODERATE, Certainty.OBSERVED),)),
            (alert4, ((Category.HEALTH, Urgency.FUTURE, Severity.MINOR, Certainty.OBSERVED),)),
        ]

        for alert, _infos in alert_info_dataset:
            for _data in _infos:
                AlertInfoFactory.create(
                    alert=alert,
                    category=_data[0],
                    urgency=_data[1],
                    severity=_data[2],
                    certainty=_data[3],
                )

        subs = [
            UserAlertSubscriptionFactory.create(
                user=self.user,
                filter_alert_country=_data[0],
                filter_alert_admin1s=_data[1],
                filter_alert_urgencies=_data[2],
                filter_alert_severities=_data[3],
                filter_alert_certainties=_data[4],
                filter_alert_categories=_data[5],
            )
            for _data in [
                (self.c_nepal, [], [], [], [], [], []),  # 0
                (self.c_nepal, [self.ad_bagmati.pk], [Urgency.IMMEDIATE], [], [], [], []),  # 1
                (self.c_nepal, [self.ad_bagmati.pk, self.ad_lalitpur.pk], [], [], [], [], []),  # 2
                (self.c_nepal, [self.ad_lalitpur.pk], [], [], [], [], []),  # 3
                (self.c_nepal, [self.ad_lalitpur.pk], [], [Severity.MODERATE], [], [], []),  # 4
                (
                    self.c_nepal,
                    [self.ad_bagmati.pk, self.ad_bhaktapur.pk],
                    [],
                    [Severity.MODERATE, Severity.MINOR],
                    [],
                    [],
                    [],
                ),  # 5
                (self.c_nepal, [self.ad_bagmati.pk], [], [Severity.UNKNOWN], [], [], []),  # 6
            ]
        ]

        assert Alert.objects.filter(is_processed_by_subscription=False).count() == len(all_alerts)
        assert UserAlertSubscription.objects.filter(user=self.user).count() == len(subs)
        assert SubscriptionAlert.objects.count() == 0

        # Run this twice to make sure re-running doesn't break anything
        for _ in range(2):
            # Make sure all_alerts are tageed as "not processed"
            Alert.objects.filter(id__in=[a.pk for a in all_alerts]).update(is_processed_by_subscription=False)
            process_pending_subscription_alerts()

            subscription_alert_map = defaultdict(set)
            for subscription_id, alert_id in SubscriptionAlert.objects.values_list('subscription_id', 'alert_id'):
                subscription_alert_map[subscription_id].add(alert_id)

            assert Alert.objects.filter(is_processed_by_subscription=False).count() == 0
            assert SubscriptionAlert.objects.count() != 0
            assert dict(subscription_alert_map) == {
                subs[0].pk: {alert1.pk, alert2.pk, alert3.pk, alert4.pk},
                subs[1].pk: {alert1.pk},
                subs[2].pk: {alert1.pk, alert2.pk, alert4.pk},
                subs[3].pk: {alert2.pk},
                subs[4].pk: {alert2.pk},
                subs[5].pk: {alert3.pk, alert4.pk},
                # Empty aren't shown here
                # subs[6].pk: {},
            }
