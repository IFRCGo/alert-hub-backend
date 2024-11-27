import strawberry
import strawberry_django

from .models import UserAlertSubscription


@strawberry_django.filters.filter(UserAlertSubscription, lookups=True)
class UserAlertSubscriptionFilter:
    id: strawberry.auto
    is_active: strawberry.auto
    notify_by_email: strawberry.auto
