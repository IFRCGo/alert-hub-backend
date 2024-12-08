from django.core.cache import caches
from django_redis.client import DefaultClient

cache: DefaultClient = caches['default']


class CacheKey:
    class RedisLockKey:
        _BASE = 'dj_lock_'
        POLL_FEED = _BASE + 'poll_feed_{}'
        TAG_EXPIRE_ALERT = _BASE + 'tag_expire_alert'
        REMOVE_EXPIRE_PROCESSED_ALERT = _BASE + 'remove_expire_processed_alert'
        SUBSCRIPTION_TAG_ALERTS = _BASE + 'subscription_tag_alerts'
        SEND_DAILY_USER_ALERT_SUBSCRIPTION_EMAIL = _BASE + 'send_daily_user_alert_subscription_email'
        SEND_WEEKLY_USER_ALERT_SUBSCRIPTION_EMAIL = _BASE + 'send_weekly_user_alert_subscription_email'
        SEND_MONTHLY_USER_ALERT_SUBSCRIPTION_EMAIL = _BASE + 'send_monthly_user_alert_subscription_email'
