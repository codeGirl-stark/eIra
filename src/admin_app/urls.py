from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_app.views import( 
    AdminUserViewSet, 
    InstitutionUserViewSet, 
    DoctorUserViewSet, 
    AssistantUserViewSet, 
    LoginView,
    ProtectedView, 
    GetUserInfo, 
    GetUserInfoById, 
    ChangePasswordView,
    ChangePseudoView,
    AdminDashboardView,
    PhotoProfileView
)

router = DefaultRouter()
router.register(r'register_admins', AdminUserViewSet, basename='admins')
router.register(r'institutions', InstitutionUserViewSet, basename='institutions')
router.register(r'doctors', DoctorUserViewSet, basename='doctors')
router.register(r'assistants', AssistantUserViewSet, basename='assistants')

router.register(r'avatar', PhotoProfileView, basename='avatar')


urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('protected/', ProtectedView.as_view(), name='protected'),
    path('userInfo', GetUserInfo.as_view(), name='user-info'),
    path('infoUser/<int:id>/', GetUserInfoById.as_view(), name='user-info-by-id'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-pseudo/', ChangePseudoView.as_view(), name='change-pseudo'),
    path('statAdmin/', AdminDashboardView.as_view(), name='statAdmin'),
    path('photoProfile/', PhotoProfileView.as_view({'get': 'list', 'post': 'create'}), name='avatar'),
]
