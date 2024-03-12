from django.urls import path

from . import views

urlpatterns = [
    path(
        'get_subscription_alerts/<int:subscription_id>/',
        views.get_subscirption_alerts,
        name='Get All Alerts Matching Subscriptions',
    ),
    path(
        'get_subscription_alerts_in_real_time/<int:subscription_id>/',
        views.get_subscription_alerts_in_real_time,
        name='Get All Alerts Matching Subscriptions Without Real Time Computation',
    ),
]
