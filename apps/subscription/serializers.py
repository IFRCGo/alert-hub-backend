from django.utils.translation import gettext
from rest_framework import serializers

from apps.cap_feed.models import Admin1
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

    def validate_filter_alert_admin1s(self, filter_alert_admin1s):
        available_admin1s_ids = set(Admin1.objects.filter(id__in=filter_alert_admin1s).values_list("id", flat=True))
        if invalid_ids := list(set(filter_alert_admin1s) - available_admin1s_ids):
            raise serializers.ValidationError(f"This Admin1 ids are missing in database: {list(invalid_ids)}")
        return filter_alert_admin1s

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        return instance
