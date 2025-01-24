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
