from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import( 
    DossierMedicalView, 
    AllDossiersMedicalView, 
    VisitesByDateView, 
    PatientView, 
    GetPatientDetail, 
    GetAllPatients,
    DossiersMedicalByPatientView,
    VisitesView,
    GetVisiteDetail,
)


# router = DefaultRouter()
# router.register(r'dossier', DossierMedicalView, basename='dossier')


urlpatterns = [
    path('patient/', PatientView.as_view(), name='patient'),##CRUD DE PATIENT
    path('patients/<int:patient_id>/', GetPatientDetail.as_view(), name='patient-detail'),##GET DETAIL D'UN PATIENT
    path('Allpatients/', GetAllPatients.as_view(), name='all-patients'),##GET TOUS LES PATIENTS DE LA BD
    
    path('dossier/', DossierMedicalView.as_view(), name='dossier'),##CRUD DOSSIER MEDICAL
    path('AllDossiers/', AllDossiersMedicalView.as_view(), name='all-dossiers'),##GET TOUS LES DOSSIERS
    path('dossier/<int:patient_id>/', DossiersMedicalByPatientView.as_view(), name='create-dossier'),##GET DOSSIER D'UN PATIENT DONNÉ
    
    path('visite/', VisitesView.as_view(), name='visite'),##CRUD DE VISITE
    path('visite_details/<int:visite_id>/', GetVisiteDetail.as_view(), name='visite-detail'),##GET DETAIL D'UNE VISITE
    path('getVisites/', VisitesByDateView.as_view(), name='visites-by-date'),##GET INFO D'UNE VISITE QUI CONCERNE UN PATIENT DONNÉ DU DOC EN LIGNE
]
