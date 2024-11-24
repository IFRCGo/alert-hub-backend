import logging
import time
import typing

from celery import shared_task
from django.db import connection, models, transaction

from apps.cap_feed.models import Alert, AlertAdmin1, AlertInfo
from apps.subscription.models import SubscriptionAlert, UserAlertSubscription
from main.cache import CacheKey
from utils.common import redis_lock

logger = logging.getLogger(__name__)


def _tb_name(model: typing.Type[models.Model]):
    return model._meta.db_table


def _cl_name(field):
    return field.field.column


TAG_MUTATION_RAW_QUERY = f'''
    WITH alert_data AS (
        SELECT
            alert.id AS id,
            alert.{_cl_name(Alert.country)} AS country_id,
            -- XXX: Remove unknown admins?
            ARRAY_REMOVE(ARRAY_AGG(distinct alert_admin1.{_cl_name(AlertAdmin1.admin1)}), NULL) AS admin1s,
            ARRAY_REMOVE(ARRAY_AGG(distinct alert_info.{_cl_name(AlertInfo.urgency)}), NULL) AS urgencies,
            ARRAY_REMOVE(ARRAY_AGG(distinct alert_info.{_cl_name(AlertInfo.severity)}), NULL) AS severities,
            ARRAY_REMOVE(ARRAY_AGG(distinct alert_info.{_cl_name(AlertInfo.certainty)}), NULL) AS certainties,
            ARRAY_REMOVE(ARRAY_AGG(distinct alert_info.{_cl_name(AlertInfo.category)}), NULL) AS categories
        FROM
            {_tb_name(Alert)} AS alert
            LEFT JOIN {_tb_name(AlertInfo)} AS alert_info ON alert_info.alert_id = alert.id
            LEFT JOIN {_tb_name(AlertAdmin1)} AS alert_admin1 ON alert_admin1.alert_id = alert.id
        WHERE alert.{_cl_name(Alert.is_processed_by_subscription)} IS FALSE
        GROUP BY alert.id, alert.country_id
    ),
    tagged_alerts AS (
        SELECT
            subscriptions.id AS subscription_id,
            alert_data.id AS alert_id
        FROM
            alert_data
            CROSS JOIN {_tb_name(UserAlertSubscription)} AS subscriptions
        WHERE
            subscriptions.{_cl_name(UserAlertSubscription.filter_alert_country)} = alert_data.country_id AND
            (
                COALESCE(array_length(subscriptions.{_cl_name(UserAlertSubscription.filter_alert_admin1s)}, 1), 0) = 0 OR
                -- subscriptions.{_cl_name(UserAlertSubscription.filter_alert_admin1s)} && alert_data.admin1s::integer[]
                subscriptions.{_cl_name(UserAlertSubscription.filter_alert_admin1s)} && alert_data.admin1s
            ) AND (
                COALESCE(array_length(subscriptions.{_cl_name(UserAlertSubscription.filter_alert_urgencies)}, 1), 0) = 0 OR
                subscriptions.{_cl_name(UserAlertSubscription.filter_alert_urgencies)} && alert_data.urgencies
            ) AND (
                COALESCE(array_length(subscriptions.{_cl_name(UserAlertSubscription.filter_alert_severities)}, 1), 0) = 0 OR
                subscriptions.{_cl_name(UserAlertSubscription.filter_alert_severities)} && alert_data.severities
            ) AND (
                COALESCE(array_length(subscriptions.{_cl_name(UserAlertSubscription.filter_alert_certainties)}, 1), 0) = 0 OR
                subscriptions.{_cl_name(UserAlertSubscription.filter_alert_certainties)} && alert_data.certainties
            ) AND (
                COALESCE(array_length(subscriptions.{_cl_name(UserAlertSubscription.filter_alert_categories)}, 1), 0) = 0 OR
                subscriptions.{_cl_name(UserAlertSubscription.filter_alert_categories)} && alert_data.categories
            )
    ),
    -- Insert tagged alerts to subscriptions
    add_tagged_alerts AS (
        INSERT INTO "{_tb_name(SubscriptionAlert)}" (
            subscription_id,
            alert_id
        ) (
            SELECT * FROM tagged_alerts
        )
    )
    -- Flag processed alerts
    UPDATE {_tb_name(Alert)}
    SET {_cl_name(Alert.is_processed_by_subscription)} = TRUE
    WHERE id in (
        SELECT id FROM alert_data
    )
'''


@shared_task
def process_pending_subscription_alerts():
    with redis_lock(CacheKey.RedisLockKey.SUBSCRIPTION_TAG_ALERTS) as acquired:
        if not acquired:
            logger.warning(f'{CacheKey.RedisLockKey.SUBSCRIPTION_TAG_ALERTS} is already running')
            return
        start_time = time.time()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(TAG_MUTATION_RAW_QUERY)
        logger.info(f'Tagged pending alerts to subscriptions. Runtime: {time.time() - start_time} seconds')
