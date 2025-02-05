from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_app.views import( 
    AdminUserViewSet, 
    DoctorUserViewSet, 
    LoginView, 
    ProtectedView, 
    GetDocteurInfo,
    GetAdminInfo, 
    GetDocteurInfoById, 
    ChangePasswordView,
    ChangePseudoView,
    AdminDashboardView
)

router = DefaultRouter()
router.register(r'register_admins', AdminUserViewSet, basename='admins')
router.register(r'doctors', DoctorUserViewSet, basename='doctors')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('infoDocteur/', GetDocteurInfo.as_view(), name='infoDocteur'),
    path('infoMedecin/<int:id>/', GetDocteurInfoById.as_view(), name='infoMedecin'),
    path('infoAdmin/', GetAdminInfo.as_view(), name='infoAdmin'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-pseudo/', ChangePseudoView.as_view(), name='change-pseudo'),
    path('statAdmin/', AdminDashboardView.as_view(), name='statAdmin'),


]
