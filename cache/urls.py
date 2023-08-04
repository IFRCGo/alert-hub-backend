from django.urls import path

from . import views

urlpatterns = [
    path('regions/', views.get_regions, name='Get countries by regions'),
    path('countries/<int:country_id>/', views.get_country, name='Get districts by country'),
    path('districts/<int:district_id>/', views.get_district, name='Get alerts by district'),
    path('infos/<int:info_id>/', views.get_info, name='Get areas by info'),
]
