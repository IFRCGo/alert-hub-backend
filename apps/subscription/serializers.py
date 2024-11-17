from django.utils.translation import gettext
from rest_framework import serializers

from apps.cap_feed.models import AlertInfo
from utils.strawberry.serializers import IntegerIDField

from .models import UserAlertSubscription


# NOTE: Make sure to sync changes here with apps/cap_feed/filters.py:AlertFilter
class UserAlertSubscriptionFilterSerializer(serializers.Serializer):
    country = IntegerIDField()
    admin1s = serializers.ListField(child=IntegerIDField())

    urgency = serializers.ListField(
        child=serializers.ChoiceField(choices=AlertInfo.Urgency.choices, required=True),
        required=False,
    )
    severity = serializers.ListField(
        child=serializers.ChoiceField(choices=AlertInfo.Severity.choices, required=True),
        required=False,
    )
    certainty = serializers.ListField(
        child=serializers.ChoiceField(choices=AlertInfo.Certainty.choices, required=True),
        required=False,
    )
    category = serializers.ListField(
        child=serializers.ChoiceField(choices=AlertInfo.Category.choices, required=True),
        required=False,
    )


class UserAlertSubscriptionSerializer(serializers.ModelSerializer):
    alert_filters = UserAlertSubscriptionFilterSerializer(required=True)

    class Meta:
        model = UserAlertSubscription
        fields = (
            "name",
            "is_active",
            "notify_by_email",
            "email_frequency",
            "alert_filters",
        )

    def validate_is_active(self, is_active):
        if is_active:
            qs = UserAlertSubscription.objects.filter(user=self.context["request"].user, is_active=True)
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

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance
