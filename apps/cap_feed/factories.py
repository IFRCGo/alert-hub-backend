import datetime

import factory
from factory.django import DjangoModelFactory

from .models import Admin1, Alert, AlertInfo, Country, Feed, Region


class RegionFactory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Sequence(lambda n: f'Region-{n}')

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Region


class CountryFactory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Sequence(lambda n: f'Country-{n}')
    iso3 = factory.Sequence(lambda n: f"{n:0>3}")

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Country


class FeedFactory(DjangoModelFactory):
    url = factory.Sequence(lambda n: f"https://source-{n}.com/test")
    format = Feed.Format.RSS
    polling_interval = Feed.PoolingInterval.I_10m

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Feed


class Admin1Factory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: 100000 + n)
    name = factory.Sequence(lambda n: f'Admin1-{n}')

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Admin1


class AlertFactory(DjangoModelFactory):
    url = factory.Sequence(lambda n: f"https://alert-{n}.com/test")
    identifier = "Identifier-X"
    sender = "Sender-X"
    sent = datetime.datetime(year=2024, month=1, day=1)
    status = Alert.Status.ACTUAL
    msg_type = Alert.MsgType.ALERT

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Alert

    @factory.post_generation
    def admin1s(self, create, extracted, **_):
        if not create:
            return
        if extracted:
            for author in extracted:
                self.admin1s.add(author)  # type: ignore[reportAttributeAccessIssue]


class AlertInfoFactory(DjangoModelFactory):
    event = "Event-X"
    category = AlertInfo.Category.HEALTH
    urgency = AlertInfo.Urgency.IMMEDIATE
    severity = AlertInfo.Severity.EXTREME
    certainty = AlertInfo.Certainty.OBSERVED

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = AlertInfo
