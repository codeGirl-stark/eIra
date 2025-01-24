from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedecinProfileView, ExportDatabaseAPIView, ImportDatabaseAPIView, PhotoProfileView


router = DefaultRouter()
router.register(r'avatar', PhotoProfileView, basename='avatar')


urlpatterns = [
    path('profile/', MedecinProfileView.as_view(), name='profileMedecin'),
    path('export/', ExportDatabaseAPIView.as_view(), name="export-database"),
    path("import/", ImportDatabaseAPIView.as_view(), name="import-database"),
    path('photoProfile/', PhotoProfileView.as_view({'get': 'list', 'post': 'create'}), name='avatar'),
]
