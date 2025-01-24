from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_app.views import AdminUserViewSet, DoctorUserViewSet, LoginView, ProtectedView, GetDocteurInfo

router = DefaultRouter()
router.register(r'register_admins', AdminUserViewSet, basename='admins')
router.register(r'doctors', DoctorUserViewSet, basename='doctors')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('infoDocteur/', GetDocteurInfo.as_view(), name='infoDocteur'),
]
