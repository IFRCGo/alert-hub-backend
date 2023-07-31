from django.urls import path

from . import views

urlpatterns = [
    path('get', views.get_countries, name='Get Cached Countries'),
    path('get/<int:country_id>/', views.get_country_by_id, name='Get Cached Countries'),
]

