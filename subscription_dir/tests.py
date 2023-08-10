import json
from graphene_django.utils.testing import GraphQLTestCase
from django.test import Client
from django.contrib.auth import get_user_model
from .models import Subscription
from .schema import create_subscription


def get_subscription(subscription_id):
    return Subscription.objects.get(id=subscription_id)


class TestCase(GraphQLTestCase):
    GRAPHQL_URL = "/subscription/graphql"
    client = Client()

    # Setup data for the tests
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        user = get_user_model()
        cls.user = user.objects.create_user(email='test1@example.com', password='testpassword')
        # Create another user
        cls.user = user.objects.create_user(email='test2@example.com', password='testpassword')
        # Create a subscription for user 1
        create_subscription(user_id=1,
                            subscription_name="test_group1",
                            country_ids=[1, 2, 3],
                            admin1_ids=[1, 2, 3],
                            urgency_array=["immediate", "expected"],
                            severity_array=["severe", "extreme"],
                            certainty_array=["observed", "likely"],
                            subscribe_by=["sms", "email"],
                            sent_flag=0)
        # Create a subscription for user 2
        create_subscription(user_id=2,
                            subscription_name="test_group2",
                            country_ids=[1, 2, 3],
                            admin1_ids=[1, 2, 3],
                            urgency_array=["immediate", "expected"],
                            severity_array=["severe", "extreme"],
                            certainty_array=["observed", "likely"],
                            subscribe_by=["sms", "email"],
                            sent_flag=0)

    def setUp(self):
        # Log in the user
        self.client.login(email='test1@example.com', password='testpassword')

    # Test query for list all subscriptions
    def test_query_list_all_subscription(self):
        response = self.query(
            '''
            query {
              listAllSubscription {
                certaintyArray
                countryIds
                admin1Ids
                id
                sentFlag
                severityArray
                subscribeBy
                subscriptionName
                urgencyArray
                userId
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['listAllSubscription']), 1)
        self.assertEqual(content['data']['listAllSubscription'][0]['id'], '1')
        self.assertEqual(content['data']['listAllSubscription'][0]['subscriptionName'],
                         'test_group1')
        self.assertEqual(content['data']['listAllSubscription'][0]['countryIds'],
                         [1, 2, 3])
        self.assertEqual(content['data']['listAllSubscription'][0]['admin1Ids'],
                         [1, 2, 3])
        self.assertEqual(content['data']['listAllSubscription'][0]['urgencyArray'],
                         ["immediate", "expected"])
        self.assertEqual(content['data']['listAllSubscription'][0]['severityArray'],
                         ["severe", "extreme"])
        self.assertEqual(content['data']['listAllSubscription'][0]['certaintyArray'],
                         ["observed", "likely"])
        self.assertEqual(content['data']['listAllSubscription'][0]['subscribeBy'],
                         ["sms", "email"])
        self.assertEqual(content['data']['listAllSubscription'][0]['sentFlag'], 0)

    # Test query for list subscriptions by filters
    def test_query_list_subscription(self):
        response = self.query(
            '''
            query {
              listSubscription(countryIds: [2,3], 
                admin1Ids: [2,3],
                urgencyArray: [], 
                severityArray: [],
                certaintyArray: []
              ) {
                id
                subscriptionName
                userId
                countryIds
                admin1Ids
                urgencyArray
                severityArray
                certaintyArray
                subscribeBy
                sentFlag
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(len(content['data']['listSubscription']), 2)

    # Test query for get subscription by id
    def test_query_get_subscription(self):
        response = self.query(
            '''
            query {
              getSubscription(subscriptionId: 1
              ) {
                id
                subscriptionName
                userId
                countryIds
                admin1Ids
                urgencyArray
                severityArray
                certaintyArray
                subscribeBy
                sentFlag
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(content['data']['getSubscription']['id'], '1')
        self.assertEqual(content['data']['getSubscription']['subscriptionName'],
                         'test_group1')
        self.assertEqual(content['data']['getSubscription']['countryIds'],
                         [1, 2, 3])
        self.assertEqual(content['data']['getSubscription']['admin1Ids'],
                         [1, 2, 3])
        self.assertEqual(content['data']['getSubscription']['urgencyArray'],
                         ["immediate", "expected"])
        self.assertEqual(content['data']['getSubscription']['severityArray'],
                         ["severe", "extreme"])
        self.assertEqual(content['data']['getSubscription']['certaintyArray'],
                         ["observed", "likely"])
        self.assertEqual(content['data']['getSubscription']['subscribeBy'],
                         ["sms", "email"])
        self.assertEqual(content['data']['getSubscription']['sentFlag'], 0)

    # Test mutation for create subscription
    def test_query_create_subscription(self):
        response = self.query(
            '''
            mutation {
              createSubscription (
                subscriptionName: "test_group3",
                countryIds: [1,2,3],
                admin1Ids: [1,2,3],
                urgencyArray: ["immediate","expected"],
                severityArray: ["severe", "extreme"],
                certaintyArray: ["observed","likely"],
                subscribeBy: ["sms", "email"],
                sentFlag: 0
              ){
                subscription {
                  id
                  subscriptionName
                  userId
                  countryIds
                  admin1Ids
                  urgencyArray
                  severityArray
                  certaintyArray
                  subscribeBy
                  sentFlag
                }
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertEqual(content['data']['createSubscription']['subscription']['id'], '3')
        self.assertEqual(content['data']['createSubscription']['subscription']['subscriptionName'],
                         'test_group3')
        self.assertEqual(content['data']['createSubscription']['subscription']['countryIds'],
                         [1, 2, 3])
        self.assertEqual(content['data']['createSubscription']['subscription']['admin1Ids'],
                         [1, 2, 3])
        self.assertEqual(content['data']['createSubscription']['subscription']['urgencyArray'],
                         ["immediate", "expected"])
        self.assertEqual(content['data']['createSubscription']['subscription']['severityArray'],
                         ["severe", "extreme"])
        self.assertEqual(content['data']['createSubscription']['subscription']['certaintyArray'],
                         ["observed", "likely"])
        self.assertEqual(content['data']['createSubscription']['subscription']['subscribeBy'],
                         ["sms", "email"])
        self.assertEqual(content['data']['createSubscription']['subscription']['sentFlag'], 0)

    # Test mutation for update subscription
    def test_query_update_subscription(self):
        response = self.query(
            '''
            mutation {
              updateSubscription (
                subscriptionId: 1
                subscriptionName: "updated_test_group1",
                countryIds: [1,2,3],
                admin1Ids: [1,2,3],
                urgencyArray: ["immediate","expected"],
                severityArray: ["severe", "extreme"],
                certaintyArray: ["observed","likely"],
                subscribeBy: ["sms", "email"],
                sentFlag: 0
              ){
                success
                errorMessage
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertTrue(content['data']['updateSubscription']['success'])
        self.assertIsNone(content['data']['updateSubscription']['errorMessage'])
        self.assertEqual(get_subscription(1).subscription_name, "updated_test_group1")

    # Test mutation for update subscription without permission
    def test_query_update_subscription_without_permission(self):
        response = self.query(
            '''
            mutation {
              updateSubscription (
                subscriptionId: 2
                subscriptionName: "updated_test_group1",
                countryIds: [1,2,3],
                admin1Ids: [1,2,3],
                urgencyArray: ["immediate","expected"],
                severityArray: ["severe", "extreme"],
                certaintyArray: ["observed","likely"],
                subscribeBy: ["sms", "email"],
                sentFlag: 0
              ){
                success
                errorMessage
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertFalse(content['data']['updateSubscription']['success'])
        self.assertIsNotNone(content['data']['updateSubscription']['errorMessage'])

    # Test mutation for delete subscription
    def test_query_delete_subscription(self):
        response = self.query(
            '''
            mutation {
              deleteSubscription (
                subscriptionId: 1
              ){
                success
                errorMessage
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertTrue(content['data']['deleteSubscription']['success'])
        self.assertIsNone(content['data']['deleteSubscription']['errorMessage'])

    # Test mutation for delete subscription without permission
    def test_query_delete_subscription_without_permission(self):
        response = self.query(
            '''
            mutation {
              deleteSubscription (
                subscriptionId: 2
              ){
                success
                errorMessage
              }
            }
            '''
        )
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        self.assertFalse(content['data']['deleteSubscription']['success'])
        self.assertIsNotNone(content['data']['deleteSubscription']['errorMessage'])
