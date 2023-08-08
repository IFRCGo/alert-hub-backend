from django.urls import path

from . import views

urlpatterns = [
    path('regions/', views.get_regions, name='Get countries by regions'),
    path('countries/<int:country_id>/', views.get_country, name='Get Admin1s by country'),
    path('admin1s/<int:admin1_id>/', views.get_admin1, name='Get alerts by admin1'),
    path('infos/<int:info_id>/', views.get_info, name='Get areas by info'),
    path('refresh/', views.refresh_cache, name='Refresh cache'),
    path('clear/', views.clear_cache, name='Clear cache'),
    path('', views.index, name='Index'),
]
