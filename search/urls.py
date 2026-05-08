from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.map_search, name='search-map'),
]
