import typing

import strawberry
import strawberry_django
from strawberry_django.pagination import OffsetPaginationInput

from apps.cap_feed.filters import AlertFilter
from apps.cap_feed.orders import AlertOrder
from apps.cap_feed.types import AlertType
from main.graphql.context import Info
from utils.strawberry.paginations import (
    CountList,
    count_list_resolver,
    pagination_field,
)

from .filters import UserAlertSubscriptionFilter
from .models import UserAlertSubscription
from .orders import UserAlertSubscriptionOrder
from .types import UserAlertSubscriptionType


@strawberry.type
class PrivateQuery:
    user_alert_subscriptions: CountList[UserAlertSubscriptionType] = pagination_field(
        pagination=True,
        filters=UserAlertSubscriptionFilter,
        order=UserAlertSubscriptionOrder,
    )

    @strawberry_django.field
    async def user_alert_subscription(self, info: Info, pk: strawberry.ID) -> UserAlertSubscriptionType | None:
        return await UserAlertSubscriptionType.get_queryset(None, None, info).filter(pk=pk).afirst()

    @strawberry_django.field
    async def subscripted_alerts(
        self,
        info: Info,
        filters: typing.Optional[AlertFilter] = strawberry.UNSET,
        order: typing.Optional[AlertOrder] = strawberry.UNSET,
        pagination: typing.Optional[OffsetPaginationInput] = strawberry.UNSET,
    ) -> CountList[AlertType]:
        queryset = AlertType.get_queryset(None, None, info).filter(
            subscriptions__in=UserAlertSubscription.objects.filter(user=info.context.request.user).all(),
        )
        # TODO: Handle duplicates from filters(frontend side) or manually
        return count_list_resolver(
            info,
            queryset,
            AlertType,
            filters=filters,  # type: ignore[reportArgumentType]
            order=order,  # type: ignore[reportArgumentType]
            pagination=pagination,  # type: ignore[reportArgumentType]
        )
