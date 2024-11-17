import strawberry

from apps.cap_feed.enums import (
    AlertInfoCategoryEnum,
    AlertInfoCertaintyEnum,
    AlertInfoSeverityEnum,
    AlertInfoUrgencyEnum,
)
from utils.strawberry.enums import get_enum_name_from_django_field

from .models import UserAlertSubscription
from .serializers import UserAlertSubscriptionFilterSerializer

UserAlertSubscriptionEmailFrequencyEnum = strawberry.enum(
    UserAlertSubscription.EmailFrequency, name='UserAlertSubscriptionEmailFrequencyEnum'
)


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in ((UserAlertSubscription.email_frequency, UserAlertSubscriptionEmailFrequencyEnum),)
}

# Custom mapping for serializers fields without model relations
enum_map.update(
    {  # type: ignore[reportCallIssue]
        get_enum_name_from_django_field(serializer().fields[field]): enum  # type: ignore[reportAttributeAccessIssue]
        for serializer, field, enum in [
            (UserAlertSubscriptionFilterSerializer, 'urgency', AlertInfoUrgencyEnum),
            (UserAlertSubscriptionFilterSerializer, 'severity', AlertInfoSeverityEnum),
            (UserAlertSubscriptionFilterSerializer, 'certainty', AlertInfoCertaintyEnum),
            (UserAlertSubscriptionFilterSerializer, 'category', AlertInfoCategoryEnum),
        ]
    }
)
