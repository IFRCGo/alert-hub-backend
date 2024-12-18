from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext
from rest_framework import serializers

from apps.cap_feed.models import Admin1
from main.tokens import TokenManager
from utils.strawberry.serializers import IntegerIDField

from .models import UserAlertSubscription


class UserAlertSubscriptionSerializer(serializers.ModelSerializer):
    # To map Int -> ID
    filter_alert_admin1s = serializers.ListField(child=IntegerIDField(required=True), required=True)

    class Meta:
        model = UserAlertSubscription
        fields = (
            "name",
            "is_active",
            "notify_by_email",
            "email_frequency",
            # Filters
            "filter_alert_country",
            "filter_alert_admin1s",
            "filter_alert_urgencies",
            "filter_alert_severities",
            "filter_alert_certainties",
            "filter_alert_categories",
        )

    def validate_is_active(self, is_active):
        if is_active:
            qs = UserAlertSubscription.objects.filter(is_active=True, user=self.context["request"].user)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.count() >= UserAlertSubscription.LIMIT_PER_USER:
                raise serializers.ValidationError(
                    gettext(
                        "Only %(limit)s active subscriptions are allowed"
                        % {
                            "limit": UserAlertSubscription.LIMIT_PER_USER,
                        }
                    )
                )
        return is_active

    def validate_filter_alert_admin1s(self, filter_alert_admin1s):
        available_admin1s_ids = set(Admin1.objects.filter(id__in=filter_alert_admin1s).values_list("id", flat=True))
        if invalid_ids := list(set(filter_alert_admin1s) - available_admin1s_ids):
            raise serializers.ValidationError(f"This Admin1 ids are missing in database: {list(invalid_ids)}")
        return filter_alert_admin1s

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance


class UserAlertSubscriptionUnsubscribeSerializer(serializers.Serializer):
    uuid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def _validate_token(self, attrs):
        token_generator = TokenManager.user_subscription_unsubscribe_generator

        try:
            uid = urlsafe_base64_decode(attrs['uuid']).decode('utf-8')
            user_subscription = UserAlertSubscription.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserAlertSubscription.DoesNotExist,
        ):
            user_subscription = None

        # TODO: Fix check_token typing
        if user_subscription is not None and token_generator.check_token(
            user_subscription,  # type: ignore[reportArgumentType]
            attrs['token'],
        ):
            return user_subscription
        raise serializers.ValidationError(
            gettext('Invalid/expired token. You may have already unsubscribed or the token has expired.')
        )

    def validate(self, attrs):
        return {
            **attrs,
            "user_subscription": self._validate_token(attrs),
        }

    def save(self, **_):
        assert isinstance(self.validated_data, dict)
        user_subscription = self.validated_data["user_subscription"]
        user_subscription.notify_by_email = False
        user_subscription.save(update_fields=("notify_by_email",))
