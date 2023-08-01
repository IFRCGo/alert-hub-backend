from django.urls import path

from . import views

urlpatterns = [
    path('get_all_regions', views.get_regions, name='Get All Cached Alerts'),
    path('get_alert/<int:alert_id>/', views.get_alert_by_id, name='Get Cached Alerts By Id'),
]

