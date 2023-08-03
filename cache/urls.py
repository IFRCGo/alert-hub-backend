from django.urls import path

from . import views

urlpatterns = [
    path('countries/', views.get_countries, name='Get countries'),
    path('districts/<int:country_id>/', views.get_districts_by_country, name='Get alerts by district'),
    path('alerts/<int:district_id>/', views.get_alerts_by_district, name='Get alerts by district'),
    path('polygons/<int:info_id>/', views.get_polygons_by_info, name='Get polygons by info'),
]
