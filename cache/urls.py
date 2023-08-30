from django.urls import path

from . import views

urlpatterns = [
    path('regions/<int:region_id>/', views.get_region, name='Get countries by region'),
    path('regions/', views.get_regions, name='Get countries by regions'),
    path('countries/<int:country_id>/', views.get_country, name='Get admin1s by country'),
    path('admin1s/<str:admin1_id>/', views.get_admin1, name='Get alerts by admin1'),
    path('infos/<int:info_id>/', views.get_info, name='Get areas by info'),
    path('alerts/summary/', views.get_alert_summary, name='Get alert summary by array of id'),
    path('alerts/<int:alert_id>/', views.get_alert, name='Get alert by id'),
    path('country_feeds/', views.get_country_feeds, name='Get country iso3 with feed urls'),
    path('country_feeds/<str:iso3>/', views.get_country_alerts, name='Get country iso3 with feed urls'),
    path('admin1s/', views.get_admin1s, name='Get admin1s by country'),
    path('', views.index, name='Index'),
    path('clear/', views.clear, name='Clear')
]
