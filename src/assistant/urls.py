from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet,
    AppointmentViewSet,
    GetDocteurPseudoView,
    AssistantProfileView,
    StatAPIView
)

urlpatterns = [
    path('profile/', AssistantProfileView.as_view(), name='profileAssistant'),
    path('getPatients/', PatientViewSet.as_view(), name='get_patients'),
    path('getPseudoDoc/', GetDocteurPseudoView.as_view(), name='get_pseudo'),
    path('rendezvous/', AppointmentViewSet.as_view(), name='get_rendezvous'),
    path('statistiques/', StatAPIView.as_view(), name='statistiques'),
]
