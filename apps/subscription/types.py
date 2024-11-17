import typing

import strawberry
import strawberry_django
from django.db import models
from strawberry_django.pagination import OffsetPaginationInput

from apps.cap_feed.filters import AlertFilter
from apps.cap_feed.orders import AlertOrder
from apps.cap_feed.types import AlertType
from main.graphql.context import Info
from utils.common import get_queryset_for_model
from utils.strawberry.enums import enum_display_field, enum_field
from utils.strawberry.paginations import CountList, count_list_resolver
from utils.strawberry.types import GenericScalar, string_field

from .models import UserAlertSubscription


@strawberry_django.type(UserAlertSubscription)
class UserAlertSubscriptionType:
    id: strawberry.ID
    created_at: strawberry.auto
    modified_at: strawberry.auto

    name = string_field(UserAlertSubscription.name)
    is_active: strawberry.auto

    alert_filters: GenericScalar

    notify_by_email: strawberry.auto
    email_frequency = enum_field(UserAlertSubscription.email_frequency)
    email_frequency_display = enum_display_field(UserAlertSubscription.email_frequency)
    email_last_sent_at: strawberry.auto

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet | None, info: Info):
        return get_queryset_for_model(UserAlertSubscription, queryset).filter(
            user=info.context.request.user,
        )

    @strawberry_django.field
    async def alerts(
        self,
        info: Info,
        root: strawberry.Parent[UserAlertSubscription],
        filters: typing.Optional[AlertFilter] = strawberry.UNSET,
        order: typing.Optional[AlertOrder] = strawberry.UNSET,
        pagination: typing.Optional[OffsetPaginationInput] = strawberry.UNSET,
    ) -> CountList[AlertType]:
        queryset = AlertType.get_queryset(None, None, info).filter(
            subscriptions=root.pk,
        )
        return count_list_resolver(
            info,
            queryset,
            AlertType,
            filters=filters,  # type: ignore[reportArgumentType]
            order=order,  # type: ignore[reportArgumentType]
            pagination=pagination,  # type: ignore[reportArgumentType]
        )
