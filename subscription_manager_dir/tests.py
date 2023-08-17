#Test Specification
#unit test

#Test add subscription and test cache
#Test change subscription and test cache
#Test delete subscription and test cache

#Test add alert and test many subscription - to - many alerts
#Test add alert and test cache delete alert and test many subscriptions to many alerts
#Test delete alert and test cache

#Test when alert is not mapped
#Test alert to be deleted is not existed test



import json
from unittest.mock import patch

from graphene_django.utils.testing import GraphQLTestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Subscription, Alert
from django.utils import timezone
from .external_alert_models import CapFeedAdmin1, CapFeedCountry, CapFeedAlert, CapFeedAlertinfo

#Since Subscription System can only have read-access to Alert DB, the tables in external models
# need to be simulated on Subscription DB, otherwise the test data will not be inserted.
#This makes sure that we could mock exact data we want on these models and test the operations
# that manipulate them.
class SubscriptionManagerTestCase(TestCase):
    # Setup data for the tests

    @classmethod
    def setUpClass(cls):
        Teyvat_1 = CapFeedCountry.objects.create(name="Teyvat_1")
        Teyvat_1.save()
        Teyvat_2 = CapFeedCountry.objects.create(name="Teyvat_2")
        Teyvat_2.save()

        # create admin data for migrations
        admin1_1 = CapFeedAdmin1.objects.create(name="Meng De", country=Teyvat_1)
        admin1_1.save()
        admin1_2 = CapFeedAdmin1.objects.create(name="Li Yue", country=Teyvat_1)
        admin1_2.save()
        admin1_3 = CapFeedAdmin1.objects.create(name="Xu Mi", country=Teyvat_2)
        admin1_3.save()
        admin1_4 = CapFeedAdmin1.objects.create(name="Feng Dan", country=Teyvat_2)
        admin1_4.save()

        #create alert data
        alert_1 = CapFeedAlert.objects.create(sent=timezone.now(), country=Teyvat_1)
        alert_1.admin1s.add(admin1_1, admin1_2)
        alert_1.save()
        alert_info_1 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Marine Weather Statement",
                                                       urgency="Expected",
                                                       severity="Minor",
                                                       certainty="Observed",
                                                       alert=alert_1)
        alert_info_2 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Thunderstormwarning",
                                                       urgency="Future",
                                                       severity="Moderate",
                                                       certainty="Likely",
                                                       alert=alert_1)
        alert_info_1.save()
        alert_info_2.save()

        alert_2 = CapFeedAlert.objects.create(sent=timezone.now(), country=Teyvat_2)
        alert_2.admin1s.add(admin1_3, admin1_4)
        alert_2.save()
        alert_info_3 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Marine Weather Statement",
                                                       urgency="Expected",
                                                       severity="Minor",
                                                       certainty="Likely",
                                                       alert=alert_2)
        alert_info_4 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Thunderstormwarning",
                                                       urgency="Immediate",
                                                       severity="Moderate",
                                                       certainty="Observed",
                                                       alert=alert_2)
        alert_info_3.save()
        alert_info_4.save()

        alert_3 = CapFeedAlert.objects.create(sent=timezone.now(), country=Teyvat_1)
        alert_3.admin1s.add(admin1_1)
        alert_3.save()
        alert_info_5 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Marine Weather Statement",
                                                       urgency="Expected",
                                                       severity="Minor",
                                                       certainty="Possible",
                                                       alert=alert_3)
        alert_info_5.save()

        alert_4 = CapFeedAlert.objects.create(sent=timezone.now(), country=Teyvat_2)
        alert_4.admin1s.add(admin1_4)
        alert_4.save()
        alert_info_6 = CapFeedAlertinfo.objects.create(category="Met",
                                                       event="Marine Weather Statement",
                                                       urgency="Expected",
                                                       severity="Severe",
                                                       certainty="Possible",
                                                       alert=alert_4)
        alert_info_6.save()

        super(SubscriptionManagerTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Clean up any resources if necessary
        super().tearDownClass()

    # Test: Creation of subscriptions and check whether subscriptions matched expected list of
    # alerts
    def test_subscription_creation_1(self):
        urgency_list = ["Expected","Future"]
        severity_list = ["Minor", "Moderate"]
        certainty_list = ["Likely", "Observed", "Possible"]
        subscription = Subscription.objects.create(subscription_name="Subscription 1",
                                                   user_id=1,
                                                   country_ids=[1],
                                                   admin1_ids=[1,2],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [1,3]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected,actual)

        #subscription.delete()

    def test_subscription_creation_2(self):
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription = Subscription.objects.create(subscription_name="Subscription 2",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[3,4],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected,actual)

        subscription.delete()


    def test_subscription_creation_all_alerts_in_country_1(self):
        urgency_list = ["Expected","Immediate","Future"]
        severity_list = ["Minor","Severe","Moderate"]
        certainty_list = ["Likely","Possible","Observed"]
        subscription = Subscription.objects.create(subscription_name="Subscription 3",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[1,2],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [1,3]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        subscription.delete()

    def test_subscription_creation_all_alerts_in_country_2(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(subscription_name="Subscription 4",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[3,4],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [2, 4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        subscription.delete()

    # Test: update subscription by severity, certainty, and urgency and check corresponding alerts
    def test_subscription_update_1(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(subscription_name="Subscription 5",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[3,4],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [2,4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        #Update urgency, severity, certainty for the subscription
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription.urgency_array = urgency_list
        subscription.severity_array = severity_list
        subscription.certainty_array = certainty_list

        subscription.save()

        expected = [4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected,actual)

        subscription.delete()

        # Test: update subscription by regions and check corresponding alerts
    def test_subscription_update_2(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(subscription_name="Subscription 6",
                                                    user_id=1,
                                                    country_ids=[2],
                                                    admin1_ids=[1, 2],
                                                    urgency_array=urgency_list,
                                                    severity_array=severity_list,
                                                    certainty_array=certainty_list,
                                                    subscribe_by=[1],
                                                    sent_flag=0)
        expected = [1, 3]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        # Update admin1 for the subscription
        admin1_ids=[3, 4]
        subscription.admin1_ids = admin1_ids
        subscription.save()

        expected = [2,4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        subscription.delete()
    # Test: delete subscription and check many subscription - to - many field
    def test_subscription_delete_1(self):
        urgency_list = ["Expected", "Immediate", "Future"]
        severity_list = ["Minor", "Severe", "Moderate"]
        certainty_list = ["Likely", "Possible", "Observed"]
        subscription = Subscription.objects.create(subscription_name="Subscription 7",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[1, 2],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [1, 3]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        # Delete the subscription
        subscription.delete()

        #Check if there is still many-to-many relationship between deleted subscriptions and
        # corresponding alerts

        for alert_id in actual:
            alert = Alert.objects.filter(id = alert_id).first()
            alert_subscriptions = alert.subscriptions.all()
            self.assertQuerysetEqual(alert_subscriptions, [])


    def test_subscription_delete_2(self):
        urgency_list = ["Expected"]
        severity_list = ["Severe"]
        certainty_list = ["Possible"]
        subscription = Subscription.objects.create(subscription_name="Subscription 8",
                                                   user_id=1,
                                                   country_ids=[2],
                                                   admin1_ids=[3, 4],
                                                   urgency_array=urgency_list,
                                                   severity_array=severity_list,
                                                   certainty_array=certainty_list,
                                                   subscribe_by=[1],
                                                   sent_flag=0)
        expected = [4]
        actual = []
        for alert in subscription.alert_set.all():
            actual.append(alert.id)
        self.assertListEqual(expected, actual)

        subscription.delete()

        #Check if there is still many-to-many relationship between deleted subscriptions and
        # corresponding alerts
        for alert_id in actual:
            alert = Alert.objects.filter(id = alert_id).first()
            alert_subscriptions = alert.subscriptions.all()
            self.assertQuerysetEqual(alert_subscriptions, [])
