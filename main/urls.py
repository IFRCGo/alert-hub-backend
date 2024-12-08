"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt

from main.graphql.schema import CustomAsyncGraphQLView
from main.graphql.schema import schema as graphql_schema
from main.views import (
    password_changed_email_preview,
    password_reset_email_preview,
    user_activation_email_preview,
    user_alert_subscription_email_preview,
)

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('health-check/', include('health_check.urls')),
    path(
        'graphql/',
        csrf_exempt(
            CustomAsyncGraphQLView.as_view(
                schema=graphql_schema,
                graphql_ide=False,
            ),
        ),
        name='graphql',
    ),
    path('', include('apps.cap_feed.urls')),
]


if settings.DEBUG:
    urlpatterns.extend(
        [
            path(
                'graphiql/',
                csrf_exempt(CustomAsyncGraphQLView.as_view(schema=graphql_schema)),
            ),
            re_path(r'^dev/email-preview/user-alert-subscription/$', user_alert_subscription_email_preview),
            re_path(r'^dev/email-preview/password-reset/$', password_reset_email_preview),
            re_path(r'^dev/email-preview/password-changed/$', password_changed_email_preview),
            re_path(r'^dev/email-preview/user-activation/$', user_activation_email_preview),
        ]
    )

    # Static and media file URLs
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
