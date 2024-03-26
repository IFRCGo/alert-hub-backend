import strawberry
import strawberry_django

from .models import Alert, Country, Feed, Region


@strawberry_django.filters.filter(Alert, lookups=True)
class AlertFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Feed, lookups=True)
class FeedFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Country, lookups=True)
class CountryFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Region, lookups=True)
class RegionFilter:
    id: strawberry.auto
