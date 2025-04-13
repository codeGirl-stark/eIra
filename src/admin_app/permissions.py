from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsActivePermission(BasePermission):
    """
    Vérifie si l'utilisateur est actif avant d'accéder aux endpoints.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_active:
            raise PermissionDenied("Votre compte est désactivé. Veuillez contacter l'administrateur.")
        return True


class IsSuperOrAdminUser(BasePermission):
    """
    Permet aux administrateurs et superusers de gérer les comptes admin.
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.is_admin)
    

class IsAssistantOfDoctor(BasePermission):
    """
    Permission qui permet aux assistants d'accéder uniquement aux données du médecin auquel ils sont affiliés.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'assistant'
    
    def has_object_permission(self, request, view, obj):
        # Vérifie que l'assistant est bien affilié au médecin propriétaire des données
        return obj.doctor == request.user.doctor