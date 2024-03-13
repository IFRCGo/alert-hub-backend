import graphene
from graphene_django import DjangoObjectType

from .models import CustomUser


class ErrorType(graphene.ObjectType):
    verifyCode = graphene.String()
    email = graphene.String()
    session = graphene.String()
    userName = graphene.String()
    user = graphene.String()


class UserType(DjangoObjectType):
    """User type object"""

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phoneNumber',
            'avatar',
            'country',
            'city',
        ]


class Query(graphene.ObjectType):
    profile = graphene.Field(UserType)

    # @login_required
    def resolve_profile(self, info, **kwargs):
        if info.context.user.is_authenticated:
            return info.context.user
        return None


class Mutation(graphene.ObjectType):
    """
    Existing Mutation
    - register
        - captch
        - verify_token using email
    - logout
    - change_email
    - forget_password
    - update_profile
        - first_name: str
        - last_name: str
        - country: str
        - city: str
        - avatar: str
    """

    ...
