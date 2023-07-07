import random
from datetime import timedelta

from uuid import uuid4

import graphene
import graphql_jwt
from graphql_jwt.decorators import login_required
from graphene_django import DjangoObjectType

from django.utils import timezone
from django.core.cache import cache

from .models import CustomUser
from .tasks import send_email
from .utils import generate_jti


class ErrorType(graphene.ObjectType):
    verifyCode = graphene.String()
    email = graphene.String()
    session = graphene.String()
    userName = graphene.String()
    user = graphene.String()


class UserType(DjangoObjectType):
    """ User type object """

    class Meta:
        model = CustomUser
        fields = [
            'email',
            'username',
            'phoneNumber',
            'avatar',
            'country',
            'city',
        ]


class Query(graphene.ObjectType):
    profile = graphene.Field(UserType)

    @login_required
    def resolve_profile(self, info, **kwargs):
        if info.context.user.is_authenticated:
            return info.context.user
        return None


class Register(graphene.Mutation):
    """ Mutation to register a user """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        verify_code = graphene.String(required=True)

    def mutate(self, info, email, password, verify_code):
        if CustomUser.objects.filter(email__iexact=email).exists():
            errors = ErrorType(email='Email already exists.')
            return Register(success=False, errors=errors)

        true_code = cache.get(email + "_register")

        if true_code is None:
            errors = ErrorType(verifyCode='Verify code has expired.')
            return Register(success=False, errors=errors)

        if verify_code != true_code:
            errors = ErrorType(verifyCode='Wrong verify code.')
            return Register(success=False, errors=errors)

        # create user
        user = CustomUser.objects.create(email=email)
        user.set_password(password)

        user.save()

        cache.delete(email)

        return Register(success=True)


class SendVerifyEmail(graphene.Mutation):
    """ Mutation for sending email verification for first registration"""

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        if CustomUser.objects.filter(email__iexact=email).exists():
            errors = ErrorType(email='Email already exists.')
            return SendVerifyEmail(success=False, errors=errors)

        email_verification_token = str(random.randint(0, 999999))
        cache.set(email + "_register", email_verification_token, 300)

        context = {
            'verification_token': email_verification_token,
        }

        send_email.delay(email, 'Activate your account.', 'email_verification.html',
                         context)

        return SendVerifyEmail(success=True)


class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        print(f"*** USER [{info.context.user}] AUTHENTICATED - VIA JWT token_auth ***")

        info.context.user.jti = generate_jti()
        info.context.user.save()

        return cls(user=info.context.user)


class ResetEmail(graphene.Mutation):
    """ Mutation to request to reset an email """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    @login_required
    def mutate(self, info):
        if info.context.user.is_authenticated:
            user = info.context.user
        else:
            errors = ErrorType(user='wrong User')
            return ResetEmail(success=False, errors=errors)

        verification_code = str(random.randint(0, 999999))
        cache.set(user.email + "_email_reset", verification_code, 300)

        user.save()

        context = {
            'reset_token': verification_code,
        }

        send_email.delay(user.email, 'Confirmation for resetting email.', 'email_reset.html',
                         context)

        return ResetEmail(success=True)


class ResetEmailConfirm(graphene.Mutation):
    """ Mutation for confirm requesting a email reset """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)
    token = graphene.String()

    class Arguments:
        verify_code = graphene.String(required=True)

    @login_required
    def mutate(self, info, verify_code):
        if info.context.user.is_authenticated:
            user = info.context.user
        else:
            errors = ErrorType(user='wrong User')
            return ResetEmailConfirm(success=False, errors=errors)

        true_code = cache.get(user.email + "_email_reset")

        if true_code is None:
            errors = ErrorType(verifyCode='Verify code has expired.')
            return ResetEmailConfirm(success=False, errors=errors)

        if verify_code != true_code:
            errors = ErrorType(verifyCode='Wrong verify code.')
            return ResetEmailConfirm(success=False, errors=errors)

        reset_token = uuid4()
        cache.set(user.email + "_confirm", reset_token, 600)

        cache.delet(user.email + "_email_reset")

        return ResetEmailConfirm(success=True, token=reset_token)


class SendNewVerifyEmail(graphene.Mutation):
    """ Mutation for requesting a password reset email """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        token = graphene.UUID(required=True)
        new_email = graphene.String(required=True)

    @login_required
    def mutate(self, info, token, new_email):

        if info.context.user.is_authenticated:
            user = info.context.user
        else:
            errors = ErrorType(user='wrong User')
            return ResetEmailConfirm(success=False, errors=errors)

        true_code = cache.get(user.email + "_confirm")

        if true_code is None:
            errors = ErrorType(session='This session has expired')
            return SendNewVerifyEmail(success=False, errors=errors)

        if CustomUser.objects.filter(email__iexact=new_email).exists():
            errors = ErrorType(email='Email already exists.')
            return SendNewVerifyEmail(success=False, errors=errors)

        if token != true_code:
            errors = ErrorType(verifyCode='Wrong verify code.')
            return SendNewVerifyEmail(success=False, errors=errors)

        email_verification_token = str(random.randint(0, 999999))
        cache.set(new_email + "_new_verify", email_verification_token, 300)

        context = {
            'verification_token': email_verification_token,
        }

        send_email.delay(new_email, 'Verify your new email.', 'email_verification.html', context)

        return SendNewVerifyEmail(success=True, token=token)


class NewEmailConfirm(graphene.Mutation):
    """ Mutation to confirm the new email. """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        new_email = graphene.String(required=True)
        verify_code = graphene.String(required=True)

    @login_required
    def mutate(self, info, new_email, verify_code):
        if info.context.user.is_authenticated:
            user = info.context.user
        else:
            errors = ErrorType(user='wrong User')
            return ResetEmailConfirm(success=False, errors=errors)

        true_code = cache.get(new_email + "_new_verify")

        if true_code is None:
            errors = ErrorType(verifyCode='Verify code has expired.')
            return NewEmailConfirm(success=False, errors=errors)

        if verify_code != true_code:
            errors = ErrorType(verifyCode='Wrong verify code.')
            return NewEmailConfirm(success=False, errors=errors)

        # create user
        user.email = new_email

        user.save()

        cache.delete(new_email + "_new_verify")

        return NewEmailConfirm(success=True)


class UpdateProfile(graphene.Mutation):
    """ Mutation to update a user's profile information """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        username = graphene.String(default_value=None)
        country = graphene.String(default_value=None)
        city = graphene.String(default_value=None)
        avatar = graphene.String(default_value=None)

    @login_required
    def mutate(self, info, username, country, city, avatar):
        user = info.context.user

        if CustomUser.objects.filter(username__iexact=username).exclude(
                pk=user.pk).exists() and username:
            errors = ErrorType(userName='usernameAlreadyExists')
            return UpdateProfile(success=False, errors=errors)

        user.username = username
        user.country = country
        user.city = city
        user.avatar = avatar
        user.save()
        return UpdateProfile(success=True)


class Logout(graphene.Mutation):
    id = graphene.ID()
    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            user = info.context.user
            if not user.is_authenticated:
                errors = ErrorType(user="User not authenticated.")
                return cls(success=False, errors=errors)

            user.jti = generate_jti()
            user.save()

            return cls(id=user.id, success=True)
        except AttributeError as error:
            return cls(success=False, errors=str(error))


class ResetPassword(graphene.Mutation):
    """ Mutation for requesting a password reset email """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            errors = ErrorType(email='Email does not exists.')
            return ResetPassword(success=False, errors=errors)

        # create email verification link
        user.password_reset_token = str(random.randint(0, 999999))
        user.password_reset_token_expires_at = timezone.now() + timedelta(minutes=5)

        user.save()

        context = {
            'reset_token': user.password_reset_token,
        }

        send_email.delay(email, 'Reset your password.', 'password_reset.html', context)

        return ResetPassword(success=True)


class ResetPasswordConfirm(graphene.Mutation):
    """ Mutation for requesting a password reset email """

    success = graphene.Boolean()
    errors = graphene.Field(ErrorType)

    class Arguments:
        verifyCode = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, verify_code, password):
        # Check if the token is empty
        if not verify_code:
            errors = ErrorType(verifyCode='Empty verify code')
            return ResetPasswordConfirm(success=False, errors=errors)

        try:
            user = CustomUser.objects.get(password_reset_token=verify_code)
        except CustomUser.DoesNotExist:
            errors = ErrorType(verifyCode='Wrong verify code.')
            return ResetPasswordConfirm(success=False, errors=errors)

        now = timezone.now()

        if user.password_reset_token_expires_at > now:
            errors = ErrorType(verifyCode='Verify code has expired.')
            return ResetPasswordConfirm(success=False, errors=errors)

        user.set_password(password)
        user.password_reset_token = uuid4()
        user.save()
        return ResetPasswordConfirm(success=True)


class Mutation(graphene.ObjectType):
    register = Register.Field()
    send_verify_email = SendVerifyEmail.Field()

    login = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    update_profile = UpdateProfile.Field()

    logout = Logout.Field()
    reset_password = ResetPassword.Field()
    reset_password_confirm = ResetPasswordConfirm.Field()
    reset_email = ResetEmail.Field()
    reset_email_confirm = ResetEmailConfirm.Field()
    send_new_verify_email = SendNewVerifyEmail.Field()
    new_email_confirm = NewEmailConfirm.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
