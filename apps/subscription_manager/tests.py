from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.cap_feed.models import Admin1 as CapFeedAdmin1
from apps.cap_feed.models import Alert as CapFeedAlert
from apps.cap_feed.models import AlertInfo as CapFeedAlertinfo
from apps.cap_feed.models import Country as CapFeedCountry

from .models import Alert, Subscription
from .subscription_alert_mapping import (
    delete_alert_to_subscription,
    map_alert_to_subscription,
    map_subscription_to_alert,
    map_subscriptions_to_alert,
)

# Since Subscription System can only have read-access to Alert DB, the tables in external models
# need to be simulated on Subscription DB, otherwise the test data will not be inserted.
# This makes sure that we could mock exact data we want on these models and test the operations
# that manipulate them.


class SubscriptionManagerTestCase(TestCase):
    # Setup data for the tests
    @classmethod
    def setUpClass(cls):
        teyvat_1 = CapFeedCountry.objects.create(name="Teyvat_1")
        teyvat_1.save()
        teyvat_2 = CapFeedCountry.objects.create(name="Teyvat_2")
        teyvat_2.save()

        # create admin data for migrations
        admin1_1 = CapFeedAdmin1.objects.create(name="Meng De", country=teyvat_1)
        admin1_1.save()
        admin1_2 = CapFeedAdmin1.objects.create(name="Li Yue", country=teyvat_1)
        admin1_2.save()
        admin1_3 = CapFeedAdmin1.objects.create(name="Xu Mi", country=teyvat_2)
        admin1_3.save()
        admin1_4 = CapFeedAdmin1.objects.create(name="Feng Dan", country=teyvat_2)
        admin1_4.save()

        # create alert data
        alert_1 = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        alert_1.admin1s.add(admin1_1, admin1_2)
        alert_1.save()
        alert_info_1 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Expected",
            severity="Minor",
            certainty="Observed",
            alert=alert_1,
        )
        alert_info_2 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Thunderstormwarning",
            urgency="Future",
            severity="Moderate",
            certainty="Likely",
            alert=alert_1,
        )
        alert_info_1.save()
        alert_info_2.save()

        alert_2 = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_2)
        alert_2.admin1s.add(admin1_3, admin1_4)
        alert_2.save()
        alert_info_3 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Expected",
            severity="Minor",
            certainty="Likely",
            alert=alert_2,
        )
        alert_info_4 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Thunderstormwarning",
            urgency="Immediate",
            severity="Moderate",
            certainty="Observed",
            alert=alert_2,
        )
        alert_info_3.save()
        alert_info_4.save()

        alert_3 = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        alert_3.admin1s.add(admin1_1)
        alert_3.save()
        alert_info_5 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Expected",
            severity="Minor",
            certainty="Possible",
            alert=alert_3,
        )
        alert_info_5.save()

        alert_4 = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_2)
        alert_4.admin1s.add(admin1_4)
        alert_4.save()
        alert_info_6 = CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Expected",
            severity="Severe",
            certainty="Possible",
            alert=alert_4,
        )
        alert_info_6.save()

        cache.clear()

        super(SubscriptionManagerTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Clean up any resources if necessary
        super().tearDownClass()

    # Test: Creation of subscriptions and check whether subscriptions matched expected list of
    # alerts
    def test_subscription_creation_1(self):
        urgency_list = ["Expected", "Future"]
        severity_list = ["Minor", "Moderate"]
        certainty_list = ["Likely", "Observed", "Possible"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 1",
            user_id=1,
            country_ids=[1],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [1, 3]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

    def test_subscription_creation_2(self):
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 2",
            user_id=1,
            country_ids=[2],
            admin1_ids=[3, 4],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)

        expected = [4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

    def test_subscription_creation_all_alerts_in_country_1(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 3",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [1, 3]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

    def test_subscription_creation_all_alerts_in_country_2(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 4",
            user_id=1,
            country_ids=[2],
            admin1_ids=[3, 4],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [2, 4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

    # Test: update subscription by severity, certainty, and urgency and check corresponding alerts
    def test_subscription_update_1(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 5",
            user_id=1,
            country_ids=[2],
            admin1_ids=[3, 4],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [2, 4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        # Update urgency, severity, certainty for the subscription
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription.urgency_array = urgency_list
        subscription.severity_array = severity_list
        subscription.certainty_array = certainty_list

        subscription.save()

        map_subscription_to_alert(subscription.pk)
        expected = [4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

        # Test: update subscription by regions and check corresponding alerts

    def test_subscription_update_2(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 6",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [1, 3]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        # Update admin1 for the subscription
        admin1_ids = [3, 4]
        subscription.admin1_ids = admin1_ids
        subscription.save()
        map_subscription_to_alert(subscription.pk)

        expected = [2, 4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

    # Test: delete subscription and check many subscription - to - many field
    def test_subscription_delete_1(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 7",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        expected = [1, 3]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        # Delete the subscription
        subscription.delete()

        # Check if there is still many-to-many relationship between deleted subscriptions and
        # corresponding alerts

        for alert in Alert.objects.filter(id__in=actual).all():
            alert_subscriptions = alert.subscriptions.all()
            self.assertQuerysetEqual(alert_subscriptions, [])

    def test_subscription_delete_2(self):
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription = Subscription.objects.create(
            subscription_name="Subscription 8",
            user_id=1,
            country_ids=[2],
            admin1_ids=[3, 4],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)

        expected = [4]
        actual = subscription.get_alert_id_list()
        self.assertListEqual(expected, actual)

        subscription.delete()

        # Check if there is still many-to-many relationship between deleted subscriptions and
        # corresponding alerts
        for alert in Alert.objects.filter(id__in=actual).all():
            alert_subscriptions = alert.subscriptions.all()
            self.assertQuerysetEqual(alert_subscriptions, [])

    # Test incoming alert that is not existed
    def test_incoming_alert_that_is_not_existed(self):
        result = map_alert_to_subscription(100)
        expected = "Alert with id 100 is not existed"
        self.assertEqual(expected, result)

    # Test incoming alert is already converted
    def test_incoming_alert_with_already_existed_id(self):
        # Create New subscription that maps the incoming alert
        urgency_list = ["Expected", "Future"]
        severity_list = ["Minor", "Moderate"]
        certainty_list = ["Likely", "Observed"]
        subscription = Subscription.objects.create(
            subscription_name="Common Subscription",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(subscription.pk)
        # Try to map alert with id 2 to the new subscription, though it is already mapped to the
        # above susbcription
        result = map_alert_to_subscription(1)
        expected = "Alert with id 1 is already converted and matched subscription"
        self.assertEqual(expected, result)

    # Test incoming alert and test if it matches the existing subscription
    def test_incoming_alert_mapping_subscription(self):
        # create the subscription
        urgency_list = ["Expected", "Future"]
        severity_list = ["Minor", "Moderate"]
        certainty_list = ["Likely", "Observed"]
        common_subscription = Subscription.objects.create(
            subscription_name="Common Subscription",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )

        # simulate the incoming alert
        teyvat_1 = CapFeedCountry.objects.get(id=1)
        admin1_1 = CapFeedAdmin1.objects.get(id=1)
        admin1_2 = CapFeedAdmin1.objects.get(id=2)
        mocked_incoming_alert = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        mocked_incoming_alert.admin1s.add(admin1_1, admin1_2)
        mocked_incoming_alert.save()
        CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Expected",
            severity="Minor",
            certainty="Observed",
            alert=mocked_incoming_alert,
        )

        # Check if the alert maps the susbcriptions
        result = map_alert_to_subscription(mocked_incoming_alert.pk)
        updated_subscription_ids = [common_subscription.pk]
        expected = (
            f"Incoming Alert {mocked_incoming_alert.pk} is successfully converted. "
            f"Mapped Subscription id "
            f"are {updated_subscription_ids}."
        )
        self.assertEqual(expected, result)

    # Test incoming alert when it is not mapped with any subscription
    def test_incoming_alert_not_mapping_subscription_cache(self):
        # simulate the incoming alert
        teyvat_1 = CapFeedCountry.objects.get(id=1)
        admin1_1 = CapFeedAdmin1.objects.get(id=1)
        mocked_incoming_alert = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        mocked_incoming_alert.admin1s.add(admin1_1)
        mocked_incoming_alert.save()
        CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Very Urgent",
            severity="Minor",
            certainty="Likely",
            alert=mocked_incoming_alert,
        )
        result = map_alert_to_subscription(mocked_incoming_alert.pk)
        expected = f"Incoming Alert {mocked_incoming_alert.pk} is not mapped with any subscription."
        self.assertEqual(expected, result)

    # Test deleted alert with id that is not existed
    def test_deleted_alert_that_is_not_existed(self):
        result = delete_alert_to_subscription(100)
        expected = "Alert with id 100 is not found in subscription database."
        self.assertEqual(expected, result)

    # Test deleted alert and test whether previously corresponded subscriptions is updated
    def test_deleted_alert_that_previously_mapped_subscription(self):
        # create the subscription
        urgency_list = ["Very Urgent"]
        severity_list = ["Minor"]
        certainty_list = ["Likely"]
        common_subscription = Subscription.objects.create(
            subscription_name="Common Subscription",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(common_subscription.pk)

        # simulate the incoming alert
        teyvat_1 = CapFeedCountry.objects.get(id=1)
        admin1_1 = CapFeedAdmin1.objects.get(id=1)
        mocked_incoming_alert = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        mocked_incoming_alert_id = mocked_incoming_alert.pk
        mocked_incoming_alert.admin1s.add(admin1_1)
        mocked_incoming_alert.save()
        CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Very Urgent",
            severity="Minor",
            certainty="Likely",
            alert=mocked_incoming_alert,
        )

        # Map the alert to the susbcriptions
        map_alert_to_subscription(mocked_incoming_alert.pk)
        # Check if subscription deletes the alert in its corresponding alert list
        result = delete_alert_to_subscription(mocked_incoming_alert_id)
        updated_subscription_ids = [common_subscription.pk]
        expected = (
            f"Alert {mocked_incoming_alert_id} is successfully "
            f"deleted from subscription database. "
            f"Updated Subscription id are "
            f"{updated_subscription_ids}."
        )
        self.assertEqual(expected, result)

    # Test deleted alert that is not mapped with any subscription(rare case)
    def test_unmapped_deleted_alerts(self):
        # create the subscription
        urgency_list = ["Very Urgent"]
        severity_list = ["Minor"]
        certainty_list = ["Likely"]
        common_subscription = Subscription.objects.create(
            subscription_name="Common Subscription",
            user_id=1,
            country_ids=[2],
            admin1_ids=[1],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )
        map_subscription_to_alert(common_subscription.pk)
        # simulate the incoming alert
        teyvat_1 = CapFeedCountry.objects.get(id=1)
        admin1_1 = CapFeedAdmin1.objects.get(id=1)
        mocked_incoming_alert = CapFeedAlert.objects.create(sent=timezone.now(), country=teyvat_1)
        mocked_incoming_alert_id = mocked_incoming_alert.pk
        mocked_incoming_alert.admin1s.add(admin1_1)
        mocked_incoming_alert.save()
        CapFeedAlertinfo.objects.create(
            category="Met",
            event="Marine Weather Statement",
            urgency="Very Urgent",
            severity="Minor",
            certainty="Likely",
            alert=mocked_incoming_alert,
        )
        # Map and then delete the corresponding subscription.
        # This will create a rare case that no subscription mapping the alerts
        map_alert_to_subscription(mocked_incoming_alert_id)
        common_subscription.delete()

        # Delete alert that is not mapped with any subscription
        result = delete_alert_to_subscription(mocked_incoming_alert_id)
        # Check results
        expected = f"Alert {mocked_incoming_alert_id} is successfully deleted " f"from subscription database. "
        self.assertEqual(expected, result)

    # Test map all subscriptions to alerts
    def test_mapping_all_subscriptions_to_alerts(self):
        urgency_list = ["Expected", "Future"]
        severity_list = ["Minor", "Moderate"]
        certainty_list = ["Likely", "Observed", "Possible"]
        subscription_1 = Subscription.objects.create(
            subscription_name="Subscriptions1",
            user_id=1,
            country_ids=[1],
            admin1_ids=[1, 2],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )

        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription_2 = Subscription.objects.create(
            subscription_name="Subscriptions2",
            user_id=1,
            country_ids=[2],
            admin1_ids=[3, 4],
            urgency_array=urgency_list,
            severity_array=severity_list,
            certainty_array=certainty_list,
            subscribe_by=[1],
            sent_flag=0,
        )

        map_subscriptions_to_alert()

        expected = [1, 3]
        actual = []
        for alert in subscription_1.alert_set.all():
            actual.append(alert.pk)
        self.assertListEqual(expected, actual)

        expected = [4]
        actual = []
        for alert in subscription_2.alert_set.all():
            actual.append(alert.pk)
        self.assertListEqual(expected, actual)
