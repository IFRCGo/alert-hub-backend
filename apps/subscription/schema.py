import os
import random
import string
from unittest.mock import patch

import graphene
from graphene_django import DjangoObjectType

from .models import Subscription

# from graphql_jwt.decorators import login_required


URGENCY_ARRAY = ["immediate", "expected", "future", "past", "unknown"]

SEVERITY_ARRAY = ["extreme", "severe", "moderate", "minor", "unknown"]

CERTAINTY_ARRAY = ["observed", "likely", "possible", "unlikely", "unknown"]


def mock_save(self: Subscription, *args, **kwargs):
    super(Subscription, self).save(*args, **kwargs)


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for _ in range(length))
    return result_str


def get_random_integer_array(start, end):
    array = []
    current = start
    while current < end:
        current = random.randint(current + 1, end)
        array.append(current)
    return array


def get_random_string_array(candicates):
    index_array = get_random_integer_array(0, len(candicates) - 1)
    string_array = []
    for index in index_array:
        string_array.append(candicates[index])
    return string_array


class SubscriptionType(DjangoObjectType):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "subscription_name",
            "user_id",
            "country_ids",
            "admin1_ids",
            "urgency_array",
            "severity_array",
            "certainty_array",
            "subscribe_by",
            "sent_flag",
        ]


def create_subscription(
    user_id,
    subscription_name,
    country_ids,
    admin1_ids,
    urgency_array,
    severity_array,
    certainty_array,
    subscribe_by,
    sent_flag,
):
    subscription = Subscription(
        user_id=user_id,
        subscription_name=subscription_name,
        country_ids=country_ids,
        admin1_ids=admin1_ids,
        urgency_array=urgency_array,
        severity_array=severity_array,
        certainty_array=certainty_array,
        subscribe_by=subscribe_by,
        sent_flag=sent_flag,
    )
    subscription.save()
    return subscription


class CreateSubscription(graphene.Mutation):
    class Arguments:
        subscription_name = graphene.String(required=True)
        country_ids = graphene.List(graphene.Int)
        admin1_ids = graphene.List(graphene.Int)
        urgency_array = graphene.List(graphene.String)
        severity_array = graphene.List(graphene.String)
        certainty_array = graphene.List(graphene.String)
        subscribe_by = graphene.List(graphene.String)
        sent_flag = graphene.Int(required=True)

    subscription = graphene.Field(SubscriptionType)

    # @login_required
    @classmethod
    def mutate(
        cls,
        info,
        subscription_name,
        country_ids,
        admin1_ids,
        urgency_array,
        severity_array,
        certainty_array,
        subscribe_by,
        sent_flag,
    ):
        subscription = create_subscription(
            info.context.user.id,
            subscription_name,
            country_ids,
            admin1_ids,
            urgency_array,
            severity_array,
            certainty_array,
            subscribe_by,
            sent_flag,
        )
        return cls(subscription=subscription)


class CreateSubscriptionTest(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        subscription_name = graphene.String(required=True)
        country_ids = graphene.List(graphene.Int)
        admin1_ids = graphene.List(graphene.Int)
        urgency_array = graphene.List(graphene.String)
        severity_array = graphene.List(graphene.String)
        certainty_array = graphene.List(graphene.String)
        subscribe_by = graphene.List(graphene.String)
        sent_flag = graphene.Int(required=True)

    subscription = graphene.Field(SubscriptionType)

    @classmethod
    def mutate(
        cls,
        info,
        user_id,
        subscription_name,
        country_ids,
        admin1_ids,
        urgency_array,
        severity_array,
        certainty_array,
        subscribe_by,
        sent_flag,
    ):
        subscription = create_subscription(
            user_id,
            subscription_name,
            country_ids,
            admin1_ids,
            urgency_array,
            severity_array,
            certainty_array,
            subscribe_by,
            sent_flag,
        )
        return cls(subscription=subscription)


class DeleteSubscription(graphene.Mutation):
    class Arguments:
        subscription_id = graphene.Int(required=True)

    success = graphene.Boolean()
    error_message = graphene.String()

    # @login_required
    @classmethod
    def mutate(cls, info, subscription_id):
        subscription = Subscription.objects.get(id=subscription_id)
        login_user_id = info.context.user.id
        if subscription.user_id != login_user_id:
            return cls(success=False, error_message='Delete operation is not authorized ' 'to this user.')
        subscription.delete()
        return cls(success=True)


class UpdateSubscription(graphene.Mutation):
    class Arguments:
        subscription_id = graphene.Int(required=True)
        subscription_name = graphene.String(required=True)
        country_ids = graphene.List(graphene.Int)
        admin1_ids = graphene.List(graphene.Int)
        urgency_array = graphene.List(graphene.String)
        severity_array = graphene.List(graphene.String)
        certainty_array = graphene.List(graphene.String)
        subscribe_by = graphene.List(graphene.String)
        sent_flag = graphene.Int(required=True)

    success = graphene.Boolean()
    error_message = graphene.String()

    @classmethod
    def mutate(
        cls,
        info,
        subscription_id,
        subscription_name,
        country_ids,
        admin1_ids,
        urgency_array,
        severity_array,
        certainty_array,
        subscribe_by,
        sent_flag,
    ):
        subscription = Subscription.objects.get(id=subscription_id)
        login_user_id = info.context.user.id
        if subscription.user_id != login_user_id:
            return cls(success=False, error_message='Update operation is not authorized ' 'to this user.')
        subscription.subscription_name = subscription_name
        subscription.country_ids = country_ids
        subscription.admin1_ids = admin1_ids
        subscription.urgency_array = urgency_array
        subscription.severity_array = severity_array
        subscription.certainty_array = certainty_array
        subscription.subscribe_by = subscribe_by
        subscription.sent_flag = sent_flag
        subscription.save()
        return cls(success=True)


@patch.object(Subscription, 'save', mock_save)
class GenerateTestSubscriptions(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        case_numbers = graphene.Int(required=True)

    success = graphene.Boolean()
    error_message = graphene.String()

    # @login_required
    @classmethod
    def mutate(cls, info, user_id, case_numbers):
        if case_numbers > 10000:
            return cls(
                success=False,
                error_message='You should not be add cases ' 'more than 10000 at one time.',
            )
        with patch.object(Subscription, 'save', mock_save):
            for _ in range(0, case_numbers):
                subscription = create_subscription(
                    user_id + random.randint(-10, 10),
                    "test_case_" + get_random_string(10),
                    get_random_integer_array(100000, 100100),
                    get_random_integer_array(1000000, 1001000),
                    get_random_string_array(URGENCY_ARRAY),
                    get_random_string_array(SEVERITY_ARRAY),
                    get_random_string_array(CERTAINTY_ARRAY),
                    ["email"],
                    0,
                )
                subscription.save()
        return cls(success=True)


class Mutation(graphene.ObjectType):
    if os.environ['TEST_MODE'] == "True":
        create_subscription_test = CreateSubscriptionTest.Field()
    create_subscription = CreateSubscription.Field()
    delete_subscription = DeleteSubscription.Field()
    update_subscription = UpdateSubscription.Field()
    generate_test_subscriptions = GenerateTestSubscriptions.Field()


class Query(graphene.ObjectType):
    list_all_subscription = graphene.List(SubscriptionType)
    list_subscription = graphene.List(
        SubscriptionType,
        country_ids=graphene.List(graphene.Int),
        admin1_ids=graphene.List(graphene.Int),
        urgency_array=graphene.List(graphene.String),
        severity_array=graphene.List(graphene.String),
        certainty_array=graphene.List(graphene.String),
    )
    get_subscription = graphene.Field(SubscriptionType, subscription_id=graphene.Int())

    # @login_required
    def resolve_list_all_subscription(self, info):
        return Subscription.objects.filter(user_id=info.context.user.id).order_by('-id')

    def resolve_list_subscription(self, info, country_ids, admin1_ids, urgency_array, severity_array, certainty_array):
        return Subscription.objects.filter(
            country_ids__contains=country_ids,
            admin1_ids__contains=admin1_ids,
            urgency_array__contains=urgency_array,
            severity_array__contains=severity_array,
            certainty_array__contains=certainty_array,
        ).order_by('-id')

    def resolve_get_subscription(self, info, subscription_id):
        return Subscription.objects.get(id=subscription_id)
