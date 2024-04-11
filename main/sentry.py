import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.strawberry import StrawberryIntegration
from strawberry.permission import BasePermission

IGNORED_ERRORS = [
    BasePermission,
]
IGNORED_LOGGERS = [
    "graphql.execution.utils",
    "strawberry.http.exceptions.HTTPException",
]

for _logger in IGNORED_LOGGERS:
    ignore_logger(_logger)


def init_sentry(app_type, tags={}, **config):
    integrations = [
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
        StrawberryIntegration(async_execution=True),
    ]
    sentry_sdk.init(
        **config,
        ignore_errors=IGNORED_ERRORS,
        integrations=integrations,
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("app_type", app_type)
        for tag, value in tags.items():
            scope.set_tag(tag, value)
