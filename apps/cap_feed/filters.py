import strawberry
import strawberry_django

from .models import Admin1, Alert, AlertInfo, Country, Feed, Region


@strawberry_django.filters.filter(Alert, lookups=True)
class AlertFilter:
    id: strawberry.auto
    url: strawberry.auto
    sender: strawberry.auto
    admin1s: strawberry.auto


@strawberry_django.filters.filter(AlertInfo, lookups=True)
class AlertInfoFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Feed, lookups=True)
class FeedFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Country, lookups=True)
class CountryFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Admin1, lookups=True)
class Admin1Filter:
    id: strawberry.auto


@strawberry_django.filters.filter(Region, lookups=True)
class RegionFilter:
    id: strawberry.auto
