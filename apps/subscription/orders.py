import strawberry
import strawberry_django

from .models import UserAlertSubscription


@strawberry_django.ordering.order(UserAlertSubscription)
class UserAlertSubscriptionOrder:
    id: strawberry.auto
    created_at: strawberry.auto
    modified_at: strawberry.auto
    name: strawberry.auto
    is_active: strawberry.auto
