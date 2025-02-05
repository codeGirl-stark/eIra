from medecin.models import Log
from rest_framework import status
from django.db.models import Count
from .models import User, UserVisit
from rest_framework import serializers
from rest_framework.views import APIView
from .permissions import IsActivePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from rest_framework import viewsets, permissions
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render
from rest_framework_simplejwt.tokens import RefreshToken
from dossierMedical.models import Patient, DossierMedical
from rest_framework.permissions import AllowAny, IsAuthenticated
from    .serializers import AdminUserSerializer, DoctorUserSerializer, LoginSerializer

User = get_user_model()

##Création de l'admin
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_admin=True)
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]


##Création du medecin
class DoctorUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_doctor=True)
    serializer_class = DoctorUserSerializer
    permission_classes = [permissions.IsAdminUser,IsActivePermission]
    
    
    def perform_create(self, serializer):
        # Enregistrer le nouvel utilisateur qui est un médecin
        serializer.save(is_doctor=True)
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, "création d'un medecin")
    
    # Action pour activer/désactiver un médecin
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, pk=None):
        doctor = self.get_object()
        doctor.is_active = not doctor.is_active  # Change l'état actif
        doctor.save()
        
        status_message = "activé" if doctor.is_active else "désactivé"
        return Response({"message": f"Le compte médecin a été {status_message} avec succès."})
    
    
    ###Action pour supprimer un medecin
    def destroy(self, request, *args, **kwargs):
        doctor = self.get_object()
        doctor.delete()  # Supprime le médecin
        
        return Response({"message": "Médecin supprimé avec succès."}, status=status.HTTP_200_OK)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
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
        
        
###View pour vérifier si le user est connecté       
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        return Response({"message": "Vous êtes authentifié"}, status=status.HTTP_200_OK)
    
    
class GetDocteurInfo(APIView):
    serializer_class = DoctorUserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Récupérer les informations du médecin connecté
        try:
            doctor = User.objects.get(email=request.user.email, is_doctor=True)
            
            # Enregistrer l'action dans les logs
            self.log_action(request.user, f"Récupération des informations du docteur {doctor.email}")
            
            serializer = self.serializer_class(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"erreur": "Médecin non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
class GetAdminInfo(APIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Récupérer les informations du médecin connecté
        try:
            admin = User.objects.get(email=request.user.email, is_admin=True)
            
            # Enregistrer l'action dans les logs
            self.log_action(request.user, f"Récupération des informations de l'administrateur {admin.email}")
            
            serializer = self.serializer_class(admin)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"erreur": "Administrateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        

class GetDocteurInfoById(APIView):
    serializer_class = DoctorUserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        # Récupérer le médecin à partir de l'ID
        doctor = get_object_or_404(User, id=id, is_doctor=True)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"Récupération des informations du docteur {doctor.email}")

        serializer = self.serializer_class(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
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
            libelle=f"{user.username} a {action}.",
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
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
#visits_last_week = Log.objects.filter(date__gte=now() - timedelta(days=7)).count()

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    # Fonction générique pour calculer les pourcentages
    def get(self, request):
        today = now().date()

        """Retourne les statistiques globales pour le tableau de bord de l'admin."""
        if not request.user.is_admin:
            return Response({"erreur": "Accès réservé aux administrateurs."}, status=403)

        # Calcul des statistiques
        total_users = User.objects.count()
        total_admin = User.objects.filter(is_admin=True).count()
        total_doctors = User.objects.filter(is_doctor=True).count()
        total_patients = Patient.objects.count()
        total_dossiers = DossierMedical.objects.count()
        total_logs = Log.objects.count()
        
        active_doctors = User.objects.filter(is_doctor=True, is_active=True).count()
        inactive_doctors = User.objects.filter(is_doctor=True, is_active=False).count()

        # Éviter la division par zéro
        doctor_percentage_active = (active_doctors / total_doctors * 100) if total_doctors > 0 else 0
        doctor_percentage_inactive = (inactive_doctors / total_doctors * 100) if total_doctors > 0 else 0

        # Fréquence de visite
        start_of_week = today - timedelta(days=today.weekday())  # Lundi de cette semaine
        start_of_last_week = start_of_week - timedelta(weeks=1)  # Lundi de la semaine passée
        start_of_month = today.replace(day=1)  # Début du mois en cours

        visits_this_week = UserVisit.objects.filter(timestamp__date__gte=start_of_week).count()
        visits_last_week = UserVisit.objects.filter(timestamp__date__gte=start_of_last_week, timestamp__date__lt=start_of_week).count()
        visits_this_month = UserVisit.objects.filter(timestamp__date__gte=start_of_month).count()

        # Calculer la croissance des visites (Éviter division par zéro)
        weekly_growth = ((visits_this_week - visits_last_week) / visits_last_week * 100) if visits_last_week > 0 else 0
        monthly_growth = ((visits_this_month - visits_last_week) / visits_last_week * 100) if visits_last_week > 0 else 0

        # Résultat
        data = {
            "total_users": total_users,
            "total_doctors": total_doctors,
            "total_admin": total_admin,
            "total_patients": total_patients,
            "total_dossiers": total_dossiers,
            "total_logs": total_logs,
            "active_doctors": active_doctors,
            "inactive_doctors": inactive_doctors,
            "doctor_percentage_active": round(doctor_percentage_active, 2),
            "doctor_percentage_inactive": round(doctor_percentage_inactive, 2),
            "visits_this_week": visits_this_week,
            "visits_last_week": visits_last_week,
            "visits_this_month": visits_this_month,
            "weekly_growth": round(weekly_growth, 2),
            "monthly_growth": round(monthly_growth, 2),
        }

        return Response(data, status=200)

    


