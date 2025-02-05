from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedecinProfileView, 
    ExportDatabaseAPIView, 
    PhotoProfileView, 
    StatAPIView, 
    LogAPIView,
    DeleteLogView,
    GlobalSearchView
)


router = DefaultRouter()
router.register(r'avatar', PhotoProfileView, basename='avatar')


urlpatterns = [
    path('profile/', MedecinProfileView.as_view(), name='profileMedecin'),
    path('logs/', LogAPIView.as_view(), name='logs'),
    path('delete-logs/', DeleteLogView.as_view(), name='delete-logs'),
    path('statistiques/', StatAPIView.as_view(), name='statistiques'),
    path('export/', ExportDatabaseAPIView.as_view(), name="export-database"),
    path('photoProfile/', PhotoProfileView.as_view({'get': 'list', 'post': 'create'}), name='avatar'),
    path('search/', GlobalSearchView.as_view(), name='autoSearch')
]
