from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedecinProfileView, 
    ExportDatabaseAPIView, 
    StatAPIView, 
    LogAPIView,
    DeleteLogView,
    GlobalSearchView
)


urlpatterns = [
    path('profile/', MedecinProfileView.as_view(), name='profileMedecin'),
    path('logs/', LogAPIView.as_view(), name='logs'),
    path('delete-logs/', DeleteLogView.as_view(), name='delete-logs'),
    path('statistiques/', StatAPIView.as_view(), name='statistiques'),
    path('export/', ExportDatabaseAPIView.as_view(), name="export-database"),
    path('search/', GlobalSearchView.as_view(), name='autoSearch')
]
