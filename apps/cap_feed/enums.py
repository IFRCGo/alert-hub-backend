import strawberry

from utils.strawberry.enums import get_enum_name_from_django_field

from .models import Alert, AlertInfo, Feed

AlertStatusEnum = strawberry.enum(Alert.Status, name='AlertStatusEnum')
AlertMsgTypeEnum = strawberry.enum(Alert.MsgType, name='AlertMsgTypeEnum')

FeedFormatEnum = strawberry.enum(Feed.Format, name='FeedFormatEnum')
FeedPoolingIntervalEnum = strawberry.enum(Feed.PoolingInterval, name='FeedPoolingIntervalEnum')
FeedStatusEnum = strawberry.enum(Feed.Status, name='FeedStatusEnum')

AlertInfoCategoryEnum = strawberry.enum(AlertInfo.Category, name='AlertInfoCategoryEnum')
AlertInfoResponseTypeEnum = strawberry.enum(AlertInfo.ResponseType, name='AlertInfoResponseTypeEnum')
AlertInfoUrgencyEnum = strawberry.enum(AlertInfo.Urgency, name='AlertInfoUrgencyEnum')
AlertInfoSeverityEnum = strawberry.enum(AlertInfo.Severity, name='AlertInfoSeverityEnum')
AlertInfoCertaintyEnum = strawberry.enum(AlertInfo.Certainty, name='AlertInfoCertaintyEnum')


enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        # Alert
        (Alert.status, AlertStatusEnum),
        (Alert.msg_type, AlertMsgTypeEnum),
        # Feed
        (Feed.format, FeedFormatEnum),
        (Feed.polling_interval, FeedPoolingIntervalEnum),
        (Feed.status, FeedStatusEnum),
        # AlertInfo
        (AlertInfo.category, AlertInfoCategoryEnum),
        (AlertInfo.response_type, AlertInfoResponseTypeEnum),
        (AlertInfo.urgency, AlertInfoUrgencyEnum),
        (AlertInfo.severity, AlertInfoSeverityEnum),
        (AlertInfo.certainty, AlertInfoCertaintyEnum),
    )
}
