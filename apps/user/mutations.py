import strawberry
from asgiref.sync import sync_to_async
from django.contrib.auth import login, logout, update_session_auth_hash

from main.graphql.context import Info
from utils.strawberry.mutations import (
    MutationEmptyResponseType,
    MutationResponseType,
    mutation_is_not_valid,
    process_input_data,
)
from utils.strawberry.transformers import convert_serializer_to_type

from .queries import UserMeType
from .serializers import (
    UserActivationSerializer,
    UserLoginSerializer,
    UserMeSerializer,
    UserPasswordChangeSerializer,
    UserPasswordResetConfirmSerializer,
    UserPasswordResetTriggerSerializer,
    UserRegisterSerializer,
)

UserLoginInput = convert_serializer_to_type(UserLoginSerializer, name="UserLoginInput")
UserRegisterInput = convert_serializer_to_type(UserRegisterSerializer, name="UserRegisterInput")
UserActivationInput = convert_serializer_to_type(UserActivationSerializer, name="UserActivationInput")

UserMeInput = convert_serializer_to_type(UserMeSerializer, partial=True, name='UserMeInput')

UserPasswordResetTriggerInput = convert_serializer_to_type(
    UserPasswordResetTriggerSerializer, name='UserPasswordResetTriggerInput'
)
UserPasswordResetConfirmInput = convert_serializer_to_type(
    UserPasswordResetConfirmSerializer, name='UserPasswordResetConfirmInput'
)

UserPasswordChangeInput = convert_serializer_to_type(UserPasswordChangeSerializer, name='UserPasswordChangeInput')


@strawberry.type
class PublicMutation:

    @strawberry.mutation
    @sync_to_async
    def login(
        self,
        data: UserLoginInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationResponseType[UserMeType]:
        serializer = UserLoginSerializer(data=process_input_data(data), context={"request": info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return MutationResponseType(
                ok=False,
                errors=errors,
            )
        assert isinstance(serializer.validated_data, dict)
        user = serializer.validated_data["user"]
        login(info.context.request, user)
        return MutationResponseType(result=user)

    @strawberry.mutation
    @sync_to_async
    def register(
        self,
        data: UserRegisterInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationEmptyResponseType:
        serializer = UserRegisterSerializer(data=process_input_data(data), context={"request": info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return MutationEmptyResponseType(
                ok=False,
                errors=errors,
            )
        serializer.save()
        return MutationEmptyResponseType()

    @strawberry.mutation
    @sync_to_async
    def account_activation(
        self,
        data: UserActivationInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationEmptyResponseType:
        serializer = UserActivationSerializer(data=process_input_data(data), context={"request": info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return MutationEmptyResponseType(
                ok=False,
                errors=errors,
            )
        serializer.save()
        # Set user activation
        return MutationEmptyResponseType()

    @strawberry.mutation
    @sync_to_async
    def password_reset_trigger(
        self,
        data: UserPasswordResetTriggerInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationEmptyResponseType:
        serializer = UserPasswordResetTriggerSerializer(
            data=process_input_data(data),
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return MutationEmptyResponseType(
                ok=False,
                errors=errors,
            )
        serializer.save()
        return MutationEmptyResponseType()

    @strawberry.mutation
    @sync_to_async
    def password_reset_confirm(
        self,
        data: UserPasswordResetConfirmInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationEmptyResponseType:
        serializer = UserPasswordResetConfirmSerializer(
            data=process_input_data(data),
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return MutationEmptyResponseType(
                ok=False,
                errors=errors,
            )
        serializer.save()
        return MutationEmptyResponseType()


@strawberry.type
class PrivateMutation:
    @strawberry.mutation
    @sync_to_async
    def logout(self, info: Info) -> MutationEmptyResponseType:
        if info.context.request.user.is_authenticated:
            logout(info.context.request)
            return MutationEmptyResponseType(ok=True)
        return MutationEmptyResponseType(ok=False)

    @strawberry.mutation
    @sync_to_async
    def change_user_password(
        self,
        data: UserPasswordChangeInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationEmptyResponseType:
        serializer = UserPasswordChangeSerializer(data=process_input_data(data), context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return MutationEmptyResponseType(
                ok=False,
                errors=errors,
            )
        serializer.save()
        update_session_auth_hash(info.context.request, info.context.request.user)  # type: ignore[reportArgumentType]
        return MutationEmptyResponseType()

    @strawberry.mutation
    @sync_to_async
    def update_me(
        self,
        data: UserMeInput,  # type: ignore[reportInvalidTypeForm]
        info: Info,
    ) -> MutationResponseType[UserMeType]:
        serializer = UserMeSerializer(
            instance=info.context.request.user,
            data=process_input_data(data),
            context={'request': info.context.request},
            partial=True,
        )
        if errors := mutation_is_not_valid(serializer):
            return MutationResponseType(
                ok=False,
                errors=errors,
            )
        user = serializer.save()
        return MutationResponseType(
            result=user,  # type: ignore[reportReturnType]
        )
