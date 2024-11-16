import logging

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext
from rest_framework import serializers

from main.tokens import TokenManager
from utils.common import get_client_ip, get_device_type
from utils.hcaptcha import CaptchaSerializerMixin

from .emails import (
    send_account_activation,
    send_password_changed_notification,
    send_password_reset,
)
from .models import User

logger = logging.getLogger(__name__)


def validate_token(attrs, token_generator) -> User:
    try:
        uid = urlsafe_base64_decode(attrs['uuid']).decode('utf-8')
        user = User.objects.get(pk=uid)
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
        user = None

    if user is not None and token_generator.check_token(user, attrs['token']):
        return user
    raise serializers.ValidationError(gettext('Invalid or expired token'))


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_password(self, password):
        validate_password(password=password)
        return password

    def validate(self, attrs):
        # NOTE: authenticate only works for active users
        authenticate_user = authenticate(
            email=attrs["email"].lower(),
            password=attrs["password"],
        )
        # User doesn't exists in the system.
        if authenticate_user is None:
            raise serializers.ValidationError(gettext("No active account found with the given credentials"))
        return {"user": authenticate_user}


# TODO: User ModelSerializer
class UserRegisterSerializer(CaptchaSerializerMixin, serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate_email(self, email) -> str:
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(gettext('This email is already registered.'))
        return email.lower()

    def validate_password(self, password):
        validate_password(password=password)
        return password

    def create(self, validated_data):
        with transaction.atomic():
            new_user = User.objects.create_user(
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                email=validated_data['email'],
                password=validated_data['password'],
                is_active=False,
            )
            transaction.on_commit(lambda: send_account_activation(new_user))
        return new_user


class UserActivationSerializer(serializers.Serializer):
    uuid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        return {**attrs, "user": validate_token(attrs, TokenManager.account_activation_token_generator)}

    def save(self, **_):
        assert isinstance(self.validated_data, dict)
        user = self.validated_data["user"]
        user.is_active = True
        user.save(update_fields=("is_active",))


class UserPasswordResetTriggerSerializer(CaptchaSerializerMixin, serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs['email'].lower()
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError(gettext("User with that email doesn't exists!!"))
        return {
            **attrs,
            'user': user,
        }

    def save(self, **_):
        assert isinstance(self.validated_data, dict)
        user = self.validated_data['user']
        client_ip = get_client_ip(self.context['request'])
        device_type = get_device_type(self.context['request'])
        send_password_reset(user=user, client_ip=client_ip, device_type=device_type)


class UserPasswordResetConfirmSerializer(CaptchaSerializerMixin, serializers.Serializer):
    uuid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, password):
        validate_password(password)
        return password

    def validate(self, attrs):
        return {**attrs, "user": validate_token(attrs, TokenManager.password_reset_token_generator)}

    def save(self, **_):
        assert isinstance(self.validated_data, dict)
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=('password',))
        client_ip = get_client_ip(self.context['request'])
        device_type = get_device_type(self.context['request'])
        transaction.on_commit(
            lambda: send_password_changed_notification(user=user, client_ip=client_ip, device_type=device_type)
        )


class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, password):
        user = self.context['request'].user
        if not user.check_password(password):
            raise serializers.ValidationError(gettext('Invalid Old Password'))
        return password

    def validate_new_password(self, password):
        validate_password(password)
        return password

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(gettext("New and old provided passwords are same"))
        return attrs

    def save(self, **_):
        assert isinstance(self.validated_data, dict)
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=('password',))
        client_ip = get_client_ip(self.context['request'])
        device_type = get_device_type(self.context['request'])
        transaction.on_commit(
            lambda: send_password_changed_notification(user=user, client_ip=client_ip, device_type=device_type)
        )


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email_opt_outs',
        )
