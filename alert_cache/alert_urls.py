from django.urls import path

from . import views

urlpatterns = [
    path('get', views.get_alerts, name='Get All Cached Alerts'),
    path('get/<int:alert_id>/', views.get_alert_by_id, name='Get Cached Alerts By Id'),
]

