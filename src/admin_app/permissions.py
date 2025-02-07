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