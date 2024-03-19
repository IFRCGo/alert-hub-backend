import strawberry
import strawberry_django

from .models import Alert, Feed, Country, Region


@strawberry_django.ordering.order(Alert)
class AlertOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Feed)
class FeedOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Country)
class CountryOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Region)
class RegionOrder:
    id: strawberry.auto
