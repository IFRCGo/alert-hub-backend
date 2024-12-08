from asgiref.sync import sync_to_async
from django.db import models
from django.utils.functional import cached_property
from strawberry.dataloader import DataLoader

from .models import SubscriptionAlert


def load_alert_count_by_subscription(keys: list[int]) -> list[int]:
    qs = (
        SubscriptionAlert.objects.filter(subscription_id__in=keys)
        .order_by()
        .values('subscription_id')
        .annotate(
            alert_count=models.Count('alert'),
        )
        .values_list('subscription_id', 'alert_count')
    )
    _map = {subscription_id: alert_count for subscription_id, alert_count in qs}
    return [_map.get(key, 0) for key in keys]


class SubscriptionDataloader:

    @cached_property
    def load_alert_count_by_subscription(self):
        return DataLoader(load_fn=sync_to_async(load_alert_count_by_subscription))
