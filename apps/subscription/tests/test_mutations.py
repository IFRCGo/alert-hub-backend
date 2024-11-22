import copy

from apps.cap_feed.factories import Admin1Factory, CountryFactory, RegionFactory
from apps.cap_feed.models import AlertInfo
from apps.subscription.factories import UserAlertSubscriptionFactory
from apps.subscription.models import UserAlertSubscription
from apps.user.factories import UserFactory
from main.tests import TestCase


class TestSubscriptionMutation(TestCase):
    class Mutation:
        CREATE_USER_ALERT_SUBSCRIPTION = '''
            mutation createUserAlertSubscription($data: UserAlertSubscriptionInput!) {
              private {
                createUserAlertSubscription(data: $data) {
                  ok
                  errors
                  result {
                    id
                    name
                    createdAt
                    modifiedAt
                    isActive

                    # Notification config
                    notifyByEmail
                    emailFrequency
                    emailFrequencyDisplay
                    emailLastSentAt

                    # Filters
                    # -- ForeignKey
                    filterAlertCountry
                    filterAlertCountryDisplay {
                      id
                      name
                    }
                    filterAlertAdmin1s
                    filterAlertAdmin1sDisplay {
                      id
                      name
                    }

                    # -- Enum
                    filterAlertUrgencies
                    filterAlertSeverities
                    filterAlertCertainties
                    filterAlertCategories
                    filterAlertUrgenciesDisplay
                    filterAlertSeveritiesDisplay
                    filterAlertCertaintiesDisplay
                    filterAlertCategoriesDisplay
                  }
                }
              }
            }
        '''

        UPDATE_USER_ALERT_SUBSCRIPTION = '''
            mutation updateUserAlertSubscription($id: ID!, $data: UserAlertSubscriptionInput!) {
              private {
                updateUserAlertSubscription(id: $id, data: $data) {
                  ok
                  errors
                  result {
                    id
                    name
                    createdAt
                    modifiedAt
                    isActive

                    # Notification config
                    notifyByEmail
                    emailFrequency
                    emailFrequencyDisplay
                    emailLastSentAt

                    # Filters
                    # -- ForeignKey
                    filterAlertCountry
                    filterAlertCountryDisplay {
                      id
                      name
                    }
                    filterAlertAdmin1s
                    filterAlertAdmin1sDisplay {
                      id
                      name
                    }

                    # -- Enum
                    filterAlertUrgencies
                    filterAlertSeverities
                    filterAlertCertainties
                    filterAlertCategories
                    filterAlertUrgenciesDisplay
                    filterAlertSeveritiesDisplay
                    filterAlertCertaintiesDisplay
                    filterAlertCategoriesDisplay
                  }
                }
              }
            }
        '''

        DELETE_USER_ALERT_SUBSCRIPTION = '''
            mutation DeleteUserAlertSubscription($id: ID!) {
              private {
                deleteUserAlertSubscription(id: $id) {
                  ok
                  errors
                  result {
                    id
                    name
                  }
                }
              }
            }
        '''

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

        self.r_asia = RegionFactory.create(name="Asia")
        self.r_europe = RegionFactory.create(name="Europe")

        self.c_nepal = CountryFactory.create(region=self.r_asia)
        self.c_india = CountryFactory.create(region=self.r_asia)
        self.c_germany = CountryFactory.create(region=self.r_europe)

        self.ad_bagmati = Admin1Factory.create(country=self.c_nepal)

        self.valid_data = dict(
            name="MySub",
            isActive=True,
            # Email
            notifyByEmail=False,
            emailFrequency=self.genum(UserAlertSubscription.EmailFrequency.MONTHLY),
            # Filter
            filterAlertCountry=self.gID(self.c_nepal.id),
            filterAlertAdmin1s=[self.gID(self.ad_bagmati.id)],
            filterAlertUrgencies=[self.genum(AlertInfo.Urgency.IMMEDIATE)],
            filterAlertSeverities=[],
            filterAlertCertainties=[],
            filterAlertCategories=[],
        )

    def create_dummy_subscription(self, user, is_active=True):
        return UserAlertSubscriptionFactory.create(
            user=user,
            is_active=is_active,
            filter_alert_country=self.c_nepal,
        )

    def _query_create(self, data, **kwargs):
        return self.query_check(
            self.Mutation.CREATE_USER_ALERT_SUBSCRIPTION,
            variables={"data": data},
            **kwargs,
        )

    def _query_update(self, id: int, data, **kwargs):
        return self.query_check(
            self.Mutation.UPDATE_USER_ALERT_SUBSCRIPTION,
            variables={"id": self.gID(id), "data": data},
            **kwargs,
        )

    def _query_delete(self, id: int, **kwargs):
        return self.query_check(
            self.Mutation.DELETE_USER_ALERT_SUBSCRIPTION,
            variables={"id": self.gID(id)},
            **kwargs,
        )

    def test_create_subscription(self):
        data = copy.deepcopy(self.valid_data)

        # Without Login session
        content = self._query_create(data, assert_errors=True)

        # Login
        self.force_login(self.user)

        # Create subscription
        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)
        self.assertEqual(sub_data["result"]["name"], data["name"], content)
        self.assertNotEqual(sub_data["result"]["id"], None, content)

    def test_create_subscription_validation_misc(self):
        self.force_login(self.user)
        data = copy.deepcopy(self.valid_data)

        # Let"s remove some fields from valid data
        data.pop("filterAlertUrgencies")
        data.pop("filterAlertSeverities")
        data.pop("filterAlertCertainties")
        data.pop("filterAlertCategories")

        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)

        # Let"s set invalid data to some of the fields
        data["filterAlertAdmin1s"] = ["hi-there", self.gID(self.ad_bagmati.id), "hi-there-again"]
        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "filterAlertAdmin1s",
                    "messages": None,
                    "object_errors": [
                        {
                            "array_errors": None,
                            "client_id": None,
                            "field": 0,
                            "messages": "A valid integer is required.",
                            "object_errors": None,
                        },
                        {
                            "array_errors": None,
                            "client_id": None,
                            "field": 2,
                            "messages": "A valid integer is required.",
                            "object_errors": None,
                        },
                    ],
                }
            ],
        )

        data["filterAlertCountry"] = "hi-there"
        data["filterAlertAdmin1s"] = []
        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "filterAlertCountry",
                    "messages": "Incorrect type. Expected pk value, received str.",
                    "object_errors": None,
                }
            ],
        )

    def test_create_subscription_validation_admin1s(self):
        self.force_login(self.user)
        data = copy.deepcopy(self.valid_data)
        data["filterAlertAdmin1s"] = [
            self.gID(self.ad_bagmati.id),
            "1000000000",
        ]

        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": [
                        {
                            "client_id": "nonMemberErrors",
                            "messages": "This Admin1 ids are missing in database: [1000000000]",
                            "object_errors": None,
                        }
                    ],
                    "client_id": None,
                    "field": "filterAlertAdmin1s",
                    "messages": None,
                    "object_errors": None,
                }
            ],
            content,
        )

    def test_create_subscription_validation_is_active(self):
        user = UserFactory.create()
        user2 = UserFactory.create()
        self.force_login(user)
        data = copy.deepcopy(self.valid_data)

        common_subs_kwargs = dict(
            filter_alert_country=self.c_nepal,
        )

        # Create dummy subscriptions
        UserAlertSubscriptionFactory.create_batch(10, is_active=False, user=user, **common_subs_kwargs)
        UserAlertSubscriptionFactory.create_batch(10, is_active=True, user=user2, **common_subs_kwargs)

        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)

        # Create dummy subscriptions to main user
        UserAlertSubscriptionFactory.create_batch(9, is_active=True, user=user, **common_subs_kwargs)
        content = self._query_create(data)
        sub_data = content["data"]["private"]["createUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "isActive",
                    "messages": "Only 10 active subscriptions are allowed",
                    "object_errors": None,
                }
            ],
        )

    def test_update_subscription(self):
        subscription = self.create_dummy_subscription(user=self.user)
        data = copy.deepcopy(self.valid_data)

        # Without Login session
        content = self._query_update(subscription.id, data, assert_errors=True)

        # Login
        self.force_login(self.user)

        # update subscription
        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)
        self.assertEqual(sub_data["result"]["name"], data["name"], content)
        self.assertNotEqual(sub_data["result"]["id"], None, content)

    def test_update_subscription_validation_misc(self):
        subscription = self.create_dummy_subscription(user=self.user)
        self.force_login(self.user)
        data = copy.deepcopy(self.valid_data)

        # Let"s remove some fields from valid data
        data.pop("filterAlertUrgencies")
        data.pop("filterAlertSeverities")
        data.pop("filterAlertCertainties")
        data.pop("filterAlertCategories")

        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)

        # Let"s set invalid data to some of the fields
        data["filterAlertAdmin1s"] = ["hi-there", self.gID(self.ad_bagmati.id), "hi-there-again"]
        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "filterAlertAdmin1s",
                    "messages": None,
                    "object_errors": [
                        {
                            "array_errors": None,
                            "client_id": None,
                            "field": 0,
                            "messages": "A valid integer is required.",
                            "object_errors": None,
                        },
                        {
                            "array_errors": None,
                            "client_id": None,
                            "field": 2,
                            "messages": "A valid integer is required.",
                            "object_errors": None,
                        },
                    ],
                }
            ],
        )

        data["filterAlertCountry"] = "hi-there"
        data["filterAlertAdmin1s"] = []
        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "filterAlertCountry",
                    "messages": "Incorrect type. Expected pk value, received str.",
                    "object_errors": None,
                }
            ],
        )

    def test_update_subscription_validation_admin1s(self):
        subscription = self.create_dummy_subscription(user=self.user)
        self.force_login(self.user)
        data = copy.deepcopy(self.valid_data)
        data["filterAlertAdmin1s"] = [
            self.gID(self.ad_bagmati.id),
            "1000000000",
        ]

        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": [
                        {
                            "client_id": "nonMemberErrors",
                            "messages": "This Admin1 ids are missing in database: [1000000000]",
                            "object_errors": None,
                        }
                    ],
                    "client_id": None,
                    "field": "filterAlertAdmin1s",
                    "messages": None,
                    "object_errors": None,
                }
            ],
            content,
        )

    def test_update_subscription_validation_is_active(self):
        user = UserFactory.create()
        user2 = UserFactory.create()

        subscription = self.create_dummy_subscription(user=user)
        other_subscription = self.create_dummy_subscription(user=user2)

        self.force_login(user)
        data = copy.deepcopy(self.valid_data)

        common_subs_kwargs = dict(
            filter_alert_country=self.c_nepal,
        )

        # update dummy subscriptions
        UserAlertSubscriptionFactory.create_batch(10, is_active=False, user=user, **common_subs_kwargs)
        UserAlertSubscriptionFactory.create_batch(10, is_active=True, user=user2, **common_subs_kwargs)

        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)

        # update dummy subscriptions to main user
        UserAlertSubscriptionFactory.create_batch(10, is_active=True, user=user, **common_subs_kwargs)
        content = self._query_update(subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "client_id": None,
                    "field": "isActive",
                    "messages": "Only 10 active subscriptions are allowed",
                    "object_errors": None,
                }
            ],
        )

        # Others subscription
        content = self._query_update(other_subscription.id, data)
        sub_data = content["data"]["private"]["updateUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "field": "nonFieldErrors",
                    "messages": "Doesn't exists in the database",
                    "object_errors": None,
                }
            ],
        )

    def test_delete_subscription(self):
        user = UserFactory.create()
        user2 = UserFactory.create()

        subscription = self.create_dummy_subscription(user=user)
        other_subscription = self.create_dummy_subscription(user=user2)

        self.force_login(user)

        content = self._query_delete(subscription.id)
        sub_data = content["data"]["private"]["deleteUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], True, content)
        self.assertEqual(sub_data["errors"], None, content)

        # Others subscription
        content = self._query_delete(other_subscription.id)
        sub_data = content["data"]["private"]["deleteUserAlertSubscription"]
        self.assertEqual(sub_data["ok"], False, content)
        self.assertNotEqual(sub_data["errors"], None, content)
        self.assertEqual(
            sub_data["errors"],
            [
                {
                    "array_errors": None,
                    "field": "nonFieldErrors",
                    "messages": "Doesn't exists in the database",
                    "object_errors": None,
                }
            ],
        )
