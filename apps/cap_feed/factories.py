import factory
from factory.django import DjangoModelFactory

from .models import Admin1, Country, Region


class RegionFactory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f'Region-{n}')

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Region


class CountryFactory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f'Country-{n}')
    iso3 = factory.Sequence(lambda n: f"{n:0>3}")

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Country


class Admin1Factory(DjangoModelFactory):
    ifrc_go_id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f'Admin1-{n}')

    class Meta:  # type: ignore[reportIncompatibleVariableOverride]
        model = Admin1
