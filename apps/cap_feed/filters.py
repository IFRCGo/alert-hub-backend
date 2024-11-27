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


@strawberry_django.filters.filter(AlertInfo, lookups=True)
class AlertInfoFilter:
    id: strawberry.auto

    def _info_enum_fields(self, field, queryset, value, prefix) -> tuple[models.QuerySet, models.Q]:
        if value:
            # NOTE: With this field, disctinct should be used by the client
            print(f"{prefix}{field}__in")
            return queryset, models.Q(**{f"{prefix}{field}__in": value})
        return queryset, models.Q()

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


@strawberry_django.filters.filter(Alert, lookups=True)
class AlertFilter:
    id: strawberry.auto
    country: strawberry.auto
    sent: strawberry.auto
    infos: AlertInfoFilter | None

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


@strawberry_django.filters.filter(Feed, lookups=True)
class FeedFilter:
    id: strawberry.auto

    def _language_field(self, field, queryset, value, prefix) -> tuple[models.QuerySet, models.Q]:
        if value:
            alias_field = f"_languageinfo_{field}_list"
            queryset = queryset.alias(
                **{
                    # NOTE: To avoid duplicate feeds when joining lanauge_info
                    alias_field: ArrayAgg(f"{prefix}languageinfo__{field}"),
                }
            )
            return queryset, models.Q(**{f"{prefix}{alias_field}__icontains": value})
        return queryset, models.Q()

    @strawberry_django.filter_field
    def name(
        self,
        queryset: models.QuerySet,
        value: str,
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        return self._language_field("name", queryset, value, prefix)


@strawberry_django.filters.filter(Country, lookups=True)
class CountryFilter:
    id: strawberry.auto


@strawberry_django.filters.filter(Admin1, lookups=True)
class Admin1Filter:
    id: strawberry.auto
    country: strawberry.auto

    @strawberry_django.filter_field
    def unknown(
        self,
        queryset: models.QuerySet,
        value: bool,
        prefix: str,
    ) -> tuple[models.QuerySet, models.Q]:
        if value:
            return queryset, models.Q(**{f"{prefix}id__lt": 0})
        return queryset, models.Q(**{f"{prefix}id__gte": 0})


@strawberry_django.filters.filter(Region, lookups=True)
class RegionFilter:
    id: strawberry.auto
