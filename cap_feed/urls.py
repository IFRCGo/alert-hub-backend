from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('feeds/', views.get_feeds, name='feeds'),
    path('inject/', views.inject, name='inject'),
]