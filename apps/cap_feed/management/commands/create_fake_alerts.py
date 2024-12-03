import factory
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cap_feed.factories import (
    Admin1Factory,
    AlertFactory,
    AlertInfoFactory,
    CountryFactory,
    FeedFactory,
    RegionFactory,
)
from apps.cap_feed.models import Admin1, AlertInfo, Country, Feed, Region
from apps.subscription.factories import UserAlertSubscriptionFactory
from apps.subscription.models import UserAlertSubscription
from apps.subscription.tasks import process_pending_subscription_alerts
from apps.user.models import User

SUBSCRIPTION_FILTERSET = [
    (
        "Sub-1",
        dict(
            filter_alert_urgencies=[AlertInfo.Urgency.IMMEDIATE],
            filter_alert_severities=[],
            filter_alert_certainties=[],
            filter_alert_categories=[],
        ),
    ),
    (
        "Sub-1",
        dict(
            filter_alert_urgencies=[AlertInfo.Urgency.IMMEDIATE, AlertInfo.Urgency.EXPECTED],
            filter_alert_severities=[AlertInfo.Severity.MODERATE],
            filter_alert_certainties=[],
            filter_alert_categories=[],
        ),
    ),
    (
        "Sub-3",
        dict(
            filter_alert_urgencies=[AlertInfo.Urgency.EXPECTED],
            filter_alert_severities=[AlertInfo.Severity.MODERATE],
            filter_alert_certainties=[AlertInfo.Certainty.LIKELY],
            filter_alert_categories=[],
        ),
    ),
    # Everything
    (
        "All",
        dict(
            filter_alert_urgencies=[],
            filter_alert_severities=[],
            filter_alert_certainties=[],
            filter_alert_categories=[],
        ),
    ),
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--user-email', dest='user_email', required=True)

    def handle(self, *_, **kwargs):
        if not settings.ALLOW_FAKE_DATA:
            self.stdout.write(
                self.style.WARNING(
                    "Add ALLOW_FAKE_DATA=true and DJANGO_DEBUG=true to environment variable to allow fake data generation"
                )
            )
            return

        user_email = kwargs['user_email']
        user = User.objects.get(email=user_email)

        FAKE_REGION_NAME = "[Fake] Asia"
        FAKE_COUNTRY_NAME = "[Fake] Nepal"
        FAKE_ADMIN1_NAME = "[Fake] Bagmati"
        FAKE_FEED_URL = "https://fake-feed.com/123"

        if (r_asia := Region.objects.filter(name=FAKE_REGION_NAME).first()) is None:
            r_asia = RegionFactory.create(name=FAKE_REGION_NAME)
        if (c_nepal := Country.objects.filter(name=FAKE_COUNTRY_NAME).first()) is None:
            c_nepal = CountryFactory.create(name=FAKE_COUNTRY_NAME, region=r_asia)
        if (ad1_bagmati := Admin1.objects.filter(name=FAKE_ADMIN1_NAME).first()) is None:
            ad1_bagmati = Admin1Factory.create(name=FAKE_ADMIN1_NAME, country=c_nepal)

        if (feed1 := Feed.objects.filter(url=FAKE_FEED_URL).first()) is None:
            feed1 = FeedFactory.create(url=FAKE_FEED_URL, country=c_nepal, polling_interval=False)

        random_id = timezone.now().isoformat()
        alert_list = AlertFactory.create_batch(
            50,
            url=factory.Sequence(lambda n: f"https://alert-{random_id}-{n}.com/test"),
            feed=feed1,
            country=c_nepal,
            admin1s=[ad1_bagmati],
            sent=timezone.now().date(),
        )

        alert_info_iterator = dict(
            category=factory.Iterator(AlertInfo.Category.choices, getter=lambda c: c[0]),
            urgency=factory.Iterator(AlertInfo.Urgency.choices, getter=lambda c: c[0]),
            severity=factory.Iterator(AlertInfo.Severity.choices, getter=lambda c: c[0]),
            certainty=factory.Iterator(AlertInfo.Certainty.choices, getter=lambda c: c[0]),
        )
        for alert in alert_list:
            AlertInfoFactory.create_batch(
                2,
                event=factory.Sequence(lambda n: f"Event-{n}"),
                alert=alert,
                **alert_info_iterator,
            )

        # Delete all existing fake subscriptions for this user
        UserAlertSubscription.objects.filter(user=user, name__startswith="[Fake]").delete()
        for name, filters in SUBSCRIPTION_FILTERSET:
            UserAlertSubscriptionFactory.create(
                name=f"[Fake] {name}",
                email_frequency=UserAlertSubscription.EmailFrequency.DAILY,
                user=user,
                filter_alert_country=c_nepal,
                filter_alert_admin1s=[ad1_bagmati.pk],
                **filters,
            )
        # Tag new alerts to subscriptions
        process_pending_subscription_alerts()
