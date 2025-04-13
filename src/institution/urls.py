from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
   InstitutionProfileView,
   InstituDashboardView
)



urlpatterns = [
    path('profileInstitu/', InstitutionProfileView.as_view(), name='profileInstitu'),
    path('statInstitu/', InstituDashboardView.as_view(), name='statInstitu'),
]
