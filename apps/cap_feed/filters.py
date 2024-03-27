import strawberry
import strawberry_django
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db import models

from .enums import (
    AlertInfoCategoryEnum,
    AlertInfoCertaintyEnum,
    AlertInfoSeverityEnum,
    AlertInfoUrgencyEnum,
)
from .models import Admin1, Alert, AlertInfo, Country, Feed, Region


@strawberry_django.filters.filter(Alert, lookups=True)
class AlertFilter:
    id: strawberry.auto
    country: strawberry.auto
    sent: strawberry.auto

    @strawberry_django.filter_field
    def region(
        self,
        queryset: models.QuerySet,
        value: strawberry.ID,
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return queryset, models.Q(**{f"{prefix}country__region": value})

    @strawberry_django.filter_field
    def admin1(
        self,
        queryset: models.QuerySet,
        value: strawberry.ID,
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return queryset, models.Q(**{f"{prefix}admin1s": value})

    def _info_enum_fields(self, field, queryset, value, prefix) -> tuple[models.QuerySet, models.Q]:
        alias_field = f"_infos_{field}_list"
        queryset = queryset.alias(
            **{
                # NOTE: To avoid duplicate alerts when joining infos
                alias_field: ArrayAgg(f"{prefix}infos__{field}"),
            }
        )
        return queryset, models.Q(**{f"{prefix}{alias_field}__overlap": value})

    @strawberry_django.filter_field
    def urgency(
        self,
        queryset: models.QuerySet,
        value: list[AlertInfoUrgencyEnum],  # type: ignore[reportInvalidTypeForm]
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return self._info_enum_fields("urgency", queryset, value, prefix)

    @strawberry_django.filter_field
    def severity(
        self,
        queryset: models.QuerySet,
        value: list[AlertInfoSeverityEnum],  # type: ignore[reportInvalidTypeForm]
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return self._info_enum_fields("severity", queryset, value, prefix)

    @strawberry_django.filter_field
    def certainty(
        self,
        queryset: models.QuerySet,
        value: list[AlertInfoCertaintyEnum],  # type: ignore[reportInvalidTypeForm]
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return self._info_enum_fields("certainty", queryset, value, prefix)

    @strawberry_django.filter_field
    def category(
        self,
        queryset: models.QuerySet,
        value: list[AlertInfoCategoryEnum],  # type: ignore[reportInvalidTypeForm]
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return self._info_enum_fields("category", queryset, value, prefix)


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
