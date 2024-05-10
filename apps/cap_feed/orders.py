import strawberry
import strawberry_django
from django.contrib.postgres.aggregates.general import StringAgg
from django.db import models

from .models import Admin1, Alert, AlertInfo, Country, Feed, Region


@strawberry_django.ordering.order(Alert)
class AlertOrder:
    id: strawberry.auto
    sent: strawberry.auto


@strawberry_django.ordering.order(AlertInfo)
class AlertInfoOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Feed)
class FeedOrder:
    id: strawberry.auto

    def _language_field(
        self,
        field,
        queryset,
        value: strawberry_django.Ordering,
        prefix,
    ) -> tuple[models.QuerySet, list[models.OrderBy]] | list[str]:
        if value:
            alias_field = f"_languageinfo_{field}_list"
            queryset = queryset.alias(
                **{
                    # NOTE: To avoid duplicate feeds when joining lanauge_info
                    alias_field: StringAgg(f"{prefix}languageinfo__{field}", " ", distinct=True),
                }
            )
            return queryset, [value.resolve(f"{prefix}{alias_field}")]
        return queryset, []

    @strawberry_django.filter_field
    def name(
        self,
        queryset: models.QuerySet,
        value: strawberry_django.Ordering,
        prefix: str,
    ) -> tuple[models.QuerySet, list[models.OrderBy]] | list[str]:
        return self._language_field("name", queryset, value, prefix)


@strawberry_django.ordering.order(Country)
class CountryOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Admin1)
class Admin1Order:
    id: strawberry.auto


@strawberry_django.ordering.order(Region)
class RegionOrder:
    id: strawberry.auto
