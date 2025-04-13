from datetime import datetime
from django.db.models import Q
from .models import Institution
from rest_framework import status
from admin_app.models import User
from django.utils.timezone import now
from medecin.models import Medecin, Log
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from .serializers import InstitutionSerializer
from medecin.serializers import MedecinSerializer
from dossierMedical.models import Patient, DossierMedical
from django.utils.timezone import now, timedelta, make_aware
from rest_framework.permissions import AllowAny, IsAuthenticated


###Vues pour modifier le profile de l'institution
class InstitutionProfileView(APIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Récupère le profil du médecin connecté."""
        try:
            institu = Institution.objects.get(user=self.request.user)
            self.log_action(self.request.user, "récupération du profil institution")
            print(institu)
            return institu  
        except Institution.DoesNotExist:
            raise NotFound({"erreur": "Profil non existant."})

    def get(self, request):
        profile = self.get_object() 
        print(profile)
        serializer = InstitutionSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        user = request.user
        self.log_action(user, "création du profil")

        if Institution.objects.filter(user=user).exists():
            return Response({"erreur": "Le profil existe déjà."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['user'] = user.id
        serializer = InstitutionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def put(self, request):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "modification du profil")
    
        # Modifier le profil de l'institution connecté
        profile = self.get_object()
        serializer = InstitutionSerializer(profile, data=request.data, partial=True)  # `partial=True` pour les mises à jour partielles
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, *args, **kwargs):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "suppression du profil")
        
        # Supprimer le profil de l'institution
        profile = self.get_object()
        profile.delete()
        return Response({"message": "Profil supprimé avec succès."}, status=status.HTTP_200_OK)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
class GetMedecinById(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MedecinSerializer

    def get(self, request, id):
        """Récupère un médecin via son ID avec son institution."""
        medecin = get_object_or_404(Medecin, user__id=id)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"Récupération des informations du docteur {medecin.user.email}")

        serializer = self.serializer_class(medecin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def log_action(self, user, action):
        """Enregistre une action dans les logs."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        

class InstituDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != 'institution':
            return Response({"erreur": "Accès réservé uniquement aux institutions."}, status=status.HTTP_403_FORBIDDEN)

        # Médecins affiliés à l’institution
        doctors = User.objects.filter(role='doctor', institution=user)
        total_doctors = doctors.count()

        # Assistants affiliés aux médecins de l’institution
        assistants = User.objects.filter(role='assistant', doctor__in=doctors)
        total_assistants = assistants.count()

        # Patients suivis par les médecins de l’institution
        patients = Patient.objects.filter(medecin__in=doctors)
        total_patients = patients.count()

        # Dossiers médicaux liés aux patients de l’institution
        dossiers = DossierMedical.objects.filter(patient__in=patients)
        total_dossiers = dossiers.count()

        # Logs générés par les médecins de l’institution (ou assistants si tu veux les inclure aussi)
        logs_institu = Log.objects.filter(medecin = user).count()
        logs_doc = Log.objects.filter(medecin__in=doctors).count()
        logs_assis = Log.objects.filter(medecin__in=assistants).count()
        total_logs = logs_institu + logs_doc + logs_assis

        # Utilisateurs actifs/inactifs : uniquement ceux de l'institution
        active_users = doctors.filter(is_active=True).count() + assistants.filter(is_active=True).count()
        inactive_users = doctors.filter(is_active=False).count() + assistants.filter(is_active=False).count()

        total_users = total_doctors + total_assistants
        users_percentage = 100  # For institution, c’est toujours 100% de ses propres users
        doctors_percentage = (total_doctors / total_users * 100) if total_users > 0 else 0
        assistants_percentage = (total_assistants / total_users * 100) if total_users > 0 else 0

        users_percentage_active = (active_users / total_users * 100) if total_users > 0 else 0
        users_percentage_inactive = (inactive_users / total_users * 100) if total_users > 0 else 0

        data = {
            "total_users": total_users,
            "users_percentage": round(users_percentage, 2),
            "total_doctors": total_doctors,
            "doctors_percentage": round(doctors_percentage, 2),
            "total_assistants": total_assistants,
            "assistants_percentage": round(assistants_percentage, 2),
            "total_patients": total_patients,
            "total_dossiers": total_dossiers,
            "total_logs": total_logs,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "users_percentage_active": round(users_percentage_active, 2),
            "users_percentage_inactive": round(users_percentage_inactive, 2),
        }

        return Response(data, status=status.HTTP_200_OK)
