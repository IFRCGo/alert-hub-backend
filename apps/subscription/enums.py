import strawberry

from apps.cap_feed.enums import (
    AlertInfoCategoryEnum,
    AlertInfoCertaintyEnum,
    AlertInfoSeverityEnum,
    AlertInfoUrgencyEnum,
)
from utils.strawberry.enums import get_enum_name_from_django_field

from .models import UserAlertSubscription

UserAlertSubscriptionEmailFrequencyEnum = strawberry.enum(
    UserAlertSubscription.EmailFrequency, name='UserAlertSubscriptionEmailFrequencyEnum'
)


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (UserAlertSubscription.email_frequency, UserAlertSubscriptionEmailFrequencyEnum),
        # Filters
        (UserAlertSubscription.filter_alert_urgencies, AlertInfoUrgencyEnum),
        (UserAlertSubscription.filter_alert_severities, AlertInfoSeverityEnum),
        (UserAlertSubscription.filter_alert_certainties, AlertInfoCertaintyEnum),
        (UserAlertSubscription.filter_alert_categories, AlertInfoCategoryEnum),
    )
}
