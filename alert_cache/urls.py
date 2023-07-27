from django.urls import path

from . import views

urlpatterns = [
    path('get', views.get_alerts, name='Get Cached Alerts'),
]

