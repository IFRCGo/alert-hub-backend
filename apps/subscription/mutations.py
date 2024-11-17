import strawberry
from asgiref.sync import sync_to_async

from main.graphql.context import Info
from utils.strawberry.mutations import (
    MutationResponseType,
    _CustomErrorType,
    mutation_is_not_valid,
    process_input_data,
)
from utils.strawberry.transformers import convert_serializer_to_type

from .queries import UserAlertSubscriptionType
from .serializers import UserAlertSubscriptionSerializer

UserAlertSubscriptionInput = convert_serializer_to_type(UserAlertSubscriptionSerializer, name="UserAlertSubscriptionInput")


@strawberry.type
class PrivateMutation:
    @strawberry.mutation
    @sync_to_async
    def create_user_alert_subcription(
        self,
        data: UserAlertSubscriptionInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationResponseType[UserAlertSubscriptionType]:
        serializer = UserAlertSubscriptionSerializer(
            # instance=info.context.request.user,
            data=process_input_data(data),
            context={'request': info.context.request},
            # partial=True,
        )
        if errors := mutation_is_not_valid(serializer):
            return MutationResponseType(
                ok=False,
                errors=errors,
            )
        obj = serializer.save()
        return MutationResponseType(
            result=obj,  # type: ignore[reportReturnType]
        )

    @strawberry.mutation
    @sync_to_async
    def update_user_alert_subcription(
        self,
        id: strawberry.ID,
        data: UserAlertSubscriptionInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationResponseType[UserAlertSubscriptionType]:
        instance = UserAlertSubscriptionType.get_queryset(None, None, info).filter(id=id).first()
        if instance is None:
            return MutationResponseType(
                ok=False,
                errors=_CustomErrorType.generate_message(message="Doesn't exists in the database"),
            )
        serializer = UserAlertSubscriptionSerializer(
            instance=instance,
            data=process_input_data(data),
            context={'request': info.context.request},
            partial=True,
        )
        if errors := mutation_is_not_valid(serializer):
            return MutationResponseType(
                ok=False,
                errors=errors,
            )
        obj = serializer.save()
        return MutationResponseType(
            result=obj,  # type: ignore[reportReturnType]
        )
