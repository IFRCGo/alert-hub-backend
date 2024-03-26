import strawberry
import strawberry_django

from main.graphql.context import Info
from utils.strawberry.paginations import CountList, pagination_field

from .filters import (
    Admin1Filter,
    AlertFilter,
    AlertInfoFilter,
    CountryFilter,
    FeedFilter,
    RegionFilter,
)
from .orders import (
    Admin1Order,
    AlertInfoOrder,
    AlertOrder,
    CountryOrder,
    FeedOrder,
    RegionOrder,
)
from .types import (
    Admin1Type,
    AlertInfoType,
    AlertType,
    CountryType,
    FeedType,
    RegionType,
)


@strawberry.type
class PublicQuery:

    regions: CountList[RegionType] = pagination_field(
        pagination=True,
        filters=RegionFilter,
        order=RegionOrder,
    )

    countries: CountList[CountryType] = pagination_field(
        pagination=True,
        filters=CountryFilter,
        order=CountryOrder,
    )

    admin1s: CountList[Admin1Type] = pagination_field(
        pagination=True,
        filters=Admin1Filter,
        order=Admin1Order,
    )

    feeds: CountList[FeedType] = pagination_field(
        pagination=True,
        filters=FeedFilter,
        order=FeedOrder,
    )

    alerts: CountList[AlertType] = pagination_field(
        pagination=True,
        filters=AlertFilter,
        order=AlertOrder,
    )

    alert_infos: CountList[AlertInfoType] = pagination_field(
        pagination=True,
        filters=AlertInfoFilter,
        order=AlertInfoOrder,
    )

    @strawberry_django.field
    async def region(self, info: Info, pk: strawberry.ID) -> RegionType | None:
        return await RegionType.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def country(self, info: Info, pk: strawberry.ID) -> CountryType | None:
        return await CountryType.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def admin1(self, info: Info, pk: strawberry.ID) -> Admin1Type | None:
        return await Admin1Type.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def feed(self, info: Info, pk: strawberry.ID) -> FeedType | None:
        return await FeedType.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def alert(self, info: Info, pk: strawberry.ID) -> AlertType | None:
        return await AlertType.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def alert_info(self, info: Info, pk: strawberry.ID) -> AlertInfoType | None:
        return await AlertInfoType.get_queryset(None, None, info).filter(pk=pk).afirst()


@strawberry.type
class PrivateQuery:
    noop: strawberry.ID = strawberry.ID('noop')
