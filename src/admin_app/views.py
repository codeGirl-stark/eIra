import os
from datetime import datetime
from medecin.models import Log
from rest_framework import status
from django.db.models import Count
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import User, UserVisit, PhotoProfil
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render
from rest_framework_simplejwt.tokens import RefreshToken
from dossierMedical.models import Patient, DossierMedical
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.timezone import now, timedelta, make_aware
from .permissions import IsActivePermission, IsSuperOrAdminUser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import (
    AdminUserSerializer, InstitutionUserSerializer, DoctorUserSerializer, 
    AssistantUserSerializer, LoginSerializer, PhotoProfilSerializer
)

User = get_user_model()

##Création de l'admin
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='ADMIN')
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]  # Seulement les superadmins peuvent gérer les admins
    
    
# Vue pour gérer les institutions
class InstitutionUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='INSTITUTION')
    serializer_class = InstitutionUserSerializer
    permission_classes = [permissions.IsAdminUser,IsActivePermission]
    
    
# Vue pour gérer les médecins
class DoctorUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='DOCTOR')
    serializer_class = DoctorUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return User.objects.filter(role="doctor")
        elif user.role == "institution":
            return User.objects.filter(role="doctor", institution=user)
        return User.objects.none()

    def perform_create(self, serializer):
        serializer.save(role='DOCTOR')
        self.log_action(self.request.user, "création d'un médecin")

    ### Action pour activer/désactiver un médecin
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def toggle_active(self, request, pk=None):
        doctor = self.get_object()
        doctor.is_active = not doctor.is_active
        doctor.save()
        status_message = "activé" if doctor.is_active else "désactivé"
        self.log_action(self.request.user, f"Medecin {status_message}")
        return Response({"message": f"Le compte médecin a été {status_message} avec succès."})

    ###Action pour supprimer un medecin
    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor.delete()
        self.log_action(self.request.user, "Suppression d'un medecin")
        return Response({"message": "Médecin supprimé avec succès."}, status=status.HTTP_200_OK)

    def log_action(self, user, action):
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )


# Vue pour gérer les assistants
class AssistantUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='ASSISTANT')
    serializer_class = AssistantUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    
    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return User.objects.filter(role="assistant")

        elif user.role == "institution":
            # Trouver tous les médecins créés par cette institution
            doctors = User.objects.filter(role="doctor", institution=user)
            return User.objects.filter(role="assistant", doctor__in=doctors)

        elif user.role == "doctor":
            return User.objects.filter(role="assistant", doctor=user)

        return User.objects.none()

    def perform_create(self, serializer):
        serializer.save(role='ASSISTANT')
        self.log_action(self.request.user, "création d'un assistant")

    ###Activer ou désactiver un assistant 
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def toggle_active(self, request, pk=None):
        assistant = self.get_object()
        assistant.is_active = not assistant.is_active
        assistant.save()
        status_message = "activé" if assistant.is_active else "désactivé"
        self.log_action(self.request.user, f"Assistant {status_message}")
        return Response({"message": f"Le compte assistant a été {status_message} avec succès."})

    ###Suppression d'un assistant
    def destroy(self, request, *args, **kwargs):
        assistant = self.get_object()
        assistant.delete()
        self.log_action(self.request.user, "Suppression d'un assistant")
        return Response({"message": "Assistant supprimé avec succès."}, status=status.HTTP_200_OK)

    def log_action(self, user, action):
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )

    
###Vue pour la connexion   
class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]  # Permet à tout le monde de tenter une connexion

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        
        # Vérification supplémentaire (déjà gérée dans le serializer)
        if not user.is_active:
            return Response(
                {"message": "Votre compte est désactivé. Veuillez contacter l'administrateur."},
                status=status.HTTP_403_FORBIDDEN
        )

        # Enregistrement de la connexion dans UserVisit
        UserVisit.objects.create(user=user, timestamp=now())
        
        # Génération des tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
        
        
###View pour avoir le profil de l'user actuellement connecté    
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        print(user.role)
        return Response({
            "message": "Vous êtes authentifié",
            "role": user.role  # Retourne uniquement le rôle
        }, status=status.HTTP_200_OK)
    
    
class GetUserInfo(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Récupère l'utilisateur connecté

        # Détermine le serializer selon le rôle
        role_serializers = {
            'admin': AdminUserSerializer,
            'institution': InstitutionUserSerializer,
            'doctor': DoctorUserSerializer,
            'assistant': AssistantUserSerializer
        }

        serializer_class = role_serializers.get(user.role)

        if serializer_class:
            self.log_action(user, f"Récupération des informations de l'utilisateur {user.email}")
            serializer = serializer_class(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"erreur": "Rôle non reconnu."}, status=status.HTTP_400_BAD_REQUEST)

    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )


class GetUserInfoById(APIView):
    serializer_classes = {
        'admin': AdminUserSerializer,
        'institution': InstitutionUserSerializer,
        'doctor': DoctorUserSerializer,
        'assistant': AssistantUserSerializer
    }
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        # Récupérer l'utilisateur à partir de l'ID
        user = get_object_or_404(User, id=id)

        # Vérifier le rôle et sélectionner le bon serializer
        serializer_class = self.serializer_classes.get(user.role)
        if not serializer_class:
            return Response({"erreur": "Type d'utilisateur inconnu."}, status=status.HTTP_400_BAD_REQUEST)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"Récupération des informations de l'utilisateur {user.email}")

        serializer = serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )    

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        new_username = request.data.get("new_username")

        # Vérifier si l'ancien mot de passe est correct
        if not check_password(old_password, user.password):
            return Response({"erreur": "L'ancien mot de passe est incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Mise à jour du mot de passe si fourni
        if new_password:
            user.set_password(new_password)

        # Mise à jour du username si fourni
        if new_username:
            user.username = new_username

        user.save()
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"Modification du mot du mot de passe de {user.email}")

        return Response({"message": "Mot de passe mis à jour avec succès."}, status=status.HTTP_200_OK)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
 
 
class ChangePseudoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_username = request.data.get("new_username")
        # Mise à jour du username si fourni
        if new_username:
            user.username = new_username

        user.save()
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"Modification du mot du pseudo de {user.email}")

        return Response({"message": "Mot de passe mis à jour avec succès."}, status=status.HTTP_200_OK)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
#visits_last_week = Log.objects.filter(date__gte=now() - timedelta(days=7)).count()

#Vue pour enregistrer et récupérer la photo de profil
class PhotoProfileView(viewsets.ModelViewSet):
    queryset = PhotoProfil.objects.all()
    serializer_class = PhotoProfilSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, "récupération de la photo de profil")
        try:
            user = self.request.user
              # L'utilisateur est récupéré à partir du token JWT
            return self.queryset.filter(user=user)
        except (PhotoProfil.DoesNotExist, TokenError):
            return PhotoProfil.objects.none()  # Retourne un queryset vide si l'utilisateur n'est pas trouvé ou le token est invalide

    def perform_create(self, serializer):
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, "création de la photo de profil")
        
        user = self.request.user  # Récupère l'utilisateur à partir du token JWT
        try:
            if PhotoProfil.objects.filter(user=user).exists():
                avatar = PhotoProfil.objects.get(user=user)
                serializer.update(avatar, serializer.validated_data)
            else:
                serializer.save(user=user)
        except (User.DoesNotExist, TokenError):
            raise ValidationError({'error': 'Invalid UID or Token'})
        
        
    def delete(self, request, *args, **kwargs):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "suppression de la photo de profil")
        
        # Récupérer l'objet PhotoProfil de l'utilisateur connecté
        photo_profile = get_object_or_404(PhotoProfil, user=request.user)

        # Vérifier si une photo de profil existe
        if photo_profile.avatar:
            # Supprimer physiquement le fichier si le chemin existe
            if os.path.exists(photo_profile.avatar.path):
                os.remove(photo_profile.avatar.path)
            
            # Supprimer la référence à la photo dans la base de données
            photo_profile.avatar = None
            photo_profile.save()

            return Response({"message": "Photo de profil supprimée avec succès."}, status=status.HTTP_200_OK)
        
        # Si aucune photo de profil n'est définie
        return Response({"message": "Aucune photo de profil à supprimer."}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    # Fonction générique pour calculer les pourcentages
    def get(self, request):
        today = datetime.today()

        """Retourne les statistiques globales pour le tableau de bord de l'admin."""
        if request.user.role != 'admin':
            return Response({"erreur": "Accès réservé aux administrateurs."}, status=status.HTTP_403_FORBIDDEN)

        # Calcul des statistiques
        total_users = User.objects.count()
        users_percentage = (total_users / total_users * 100) if total_users > 0 else 0
        
        total_admins = User.objects.filter(role='admin').count()
        admin_percentage = (total_admins / total_users * 100) if total_users > 0 else 0
         
        total_institutions = User.objects.filter(role='institution').count()
        institu_percentage = (total_institutions / total_users * 100) if total_users > 0 else 0
        
        total_doctors = User.objects.filter(role='doctor').count()
        doctors_percentage = (total_doctors / total_users * 100) if total_users > 0 else 0
        
        total_assistants = User.objects.filter(role='assistant').count()
        assistants_percentage = (total_assistants / total_users * 100) if total_users > 0 else 0
        
        total_patients = Patient.objects.count()
        total_dossiers = DossierMedical.objects.count()
        total_logs = Log.objects.count()
        
        # Comptage des utilisateurs actifs/inactifs
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
    

        # Éviter la division par zéro pour les pourcentages
        users_percentage_active = (active_users / total_users * 100) if total_users > 0 else 0
        users_percentage_inactive = (inactive_users / total_users * 100) if total_users > 0 else 0


        # Fréquence de visite
        start_of_week = today - timedelta(days=today.weekday())  # Lundi de cette semaine
        start_of_last_week = start_of_week - timedelta(weeks=1)  # Lundi de la semaine passée
        start_of_month = today.replace(day=1)  # Début du mois en cours

        # Rendre start_of_week, start_of_last_week et start_of_month "timezone-aware"
        start_of_week = make_aware(datetime.combine(start_of_week, datetime.min.time()))
        start_of_last_week = make_aware(datetime.combine(start_of_last_week, datetime.min.time()))
        start_of_month = make_aware(datetime.combine(start_of_month, datetime.min.time()))

        # Filtrage en utilisant `timestamp__gte` au lieu de `timestamp__date__gte`
        visits_this_week = UserVisit.objects.filter(timestamp__gte=start_of_week).count()
        visits_last_week = UserVisit.objects.filter(timestamp__gte=start_of_last_week, timestamp__lt=start_of_week).count()
        visits_this_month = UserVisit.objects.filter(timestamp__gte=start_of_month).count()
    
        # Calculer la croissance des visites (Éviter division par zéro)
        weekly_growth = ((visits_this_week - visits_last_week) / visits_last_week * 100) if visits_last_week > 0 else 0
        monthly_growth = ((visits_this_month - visits_last_week) / visits_last_week * 100) if visits_last_week > 0 else 0

        # Résultat
        data = {
            "total_users": total_users,
            "users_percentage":round(users_percentage, 2),
            "total_admins": total_admins,
            "admin_percentage":round(admin_percentage, 2),
            "total_institutions": total_institutions,
            "institu_percentage":round(institu_percentage, 2),
            "total_doctors": total_doctors,
            "doctors_percentage":round(doctors_percentage, 2),
            "total_assistants": total_assistants,
            "assistants_percentage" : round(assistants_percentage, 2),
            "total_patients": total_patients,
            "total_dossiers": total_dossiers,
            "total_logs": total_logs,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "users_percentage_active": round(users_percentage_active, 2),
            "users_percentage_inactive": round(users_percentage_inactive, 2),
            "visits_this_week": visits_this_week,
            "visits_last_week": visits_last_week,
            "visits_this_month": visits_this_month,
            "weekly_growth": round(weekly_growth, 2),
            "monthly_growth": round(monthly_growth, 2),
        }

        return Response(data, status=200)

    


