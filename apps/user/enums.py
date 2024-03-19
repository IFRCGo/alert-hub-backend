import strawberry

from utils.strawberry.enums import get_enum_name_from_django_field

from .models import User

OptEmailNotificationTypeEnum = strawberry.enum(User.OptEmailNotificationType, name='OptEmailNotificationTypeEnum')


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (User.email_opt_outs, OptEmailNotificationTypeEnum),
    )
}
