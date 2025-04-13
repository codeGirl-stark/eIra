from medecin.models import Log
from rest_framework import status
from admin_app.models import User
from rest_framework import generics
from django.utils.timezone import now
from dossierMedical import serializers
from rest_framework.views import APIView
from django.utils.timezone import make_aware
from rest_framework.response import Response
from datetime import datetime, timedelta, time
from django.db.models.functions import TruncDate
from .models import DossierMedical,Patient, Visite
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import DossierMedicalSerializer, PatientSerializer,VisiteSerializer


####Vue pour CRUD un patient
class PatientView(APIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "création d'un patient")
        
        """Créer un patient pour le médecin connecté."""
        if not request.user.role == "doctor":
            return Response({"erreur": "Seuls les médecins peuvent créer des patients."}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data.copy()
        data['medecin'] = request.user.id
        
        serializer = PatientSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "récupération des informations des patients enregistrés.")
        
        """Obtenir les patients associés au médecin connecté."""
        if not request.user.role == "doctor":
            return Response({"erreur": "Seuls les médecins peuvent consulter leurs patients."}, status=status.HTTP_403_FORBIDDEN)
        try : 
            patients = Patient.objects.filter(medecin=request.user)
            serializer = PatientSerializer(patients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)


    def put(self, request):
        """Modifier un patient existant."""
        patient_id = request.data.get("id")
        if not patient_id:
            return Response({"erreur": "L'identifiant du patient est requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id, medecin=request.user)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"modification des informations du patient{patient.nom} {patient.prenom}")
        
        
        serializer = PatientSerializer(patient, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        """Supprimer un patient."""
        patient_id = request.data.get("id")
        if not patient_id:
            return Response({"erreur": "L'ID du patient est requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id, medecin=request.user)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"suppression du patient {patient.nom} {patient.prenom}")
        
        patient.delete()
        return Response({"message": "Patient supprimé avec succès."}, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    

###Vue pour obtenir les informations d'un patient spécifique
class GetPatientDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        """Obtenir les informations d'un patient spécifique."""
        try:
            patient = Patient.objects.get(id=patient_id, medecin=request.user)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, f"récupération des informations du patient {patient.nom} {patient.prenom}")
        
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )

##Vue pour récupérer tous les patients
class GetAllPatients(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ADMIN → Tous les patients
        if user.role == "admin":
            patients = Patient.objects.all()
            self.log_action(user, "a récupéré tous les patients de la base de données")

        # INSTITUTION → Patients des médecins qu’elle a créés
        elif user.role == "institution":
            doctors = User.objects.filter(role="doctor", institution=user)
            patients = Patient.objects.filter(medecin__in=doctors)
            self.log_action(user, "a récupéré les patients de ses médecins")

        else:
            return Response({"erreur": "Accès réservé aux administrateurs et institutions."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def log_action(self, user, action):
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )

    
###Vues pour créer, modifier et supprimer un dossier médical
class DossierMedicalView(APIView):
    queryset = DossierMedical.objects.all()
    serializer_class = DossierMedicalSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Créer un dossier médical pour un patient spécifique."""
        patient_id = request.data.get("patient")
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, f"création du dossier médical du patient {patient.nom} {patient.prenom}")
        

        data = request.data.copy()
        data['patient'] = patient_id  # Associer le patient
        serializer = DossierMedicalSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    ##Modification du dossier médica&l
    def put(self, request):
        """Modifier un dossier médical d'un patient spécifique."""
        patient_id = request.data.get("patient")
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)

        num_dossier = request.data.get("numDossier")
        if not num_dossier:
            return Response({"erreur": "Le champ 'numDossier' est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(numDossier=num_dossier, patient=patient)
        except DossierMedical.DoesNotExist:
            return Response({"erreur": "Dossier médical introuvable pour ce patient."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"modification du dossier médical {num_dossier}")
        

        serializer = DossierMedicalSerializer(dossier, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ##Suppression du dossier médical avec condition date rdv sup à date du jour
    def delete(self, request, patient_id):
        """Supprimer un dossier médical d'un patient spécifique."""
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)

        num_dossier = request.data.get("numDossier")
        if not num_dossier:
            return Response({"erreur": "Le champ 'numDossier' est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dossier = DossierMedical.objects.get(numDossier=num_dossier, patient=patient)
        except DossierMedical.DoesNotExist:
            return Response({"erreur": "Dossier médical introuvable pour ce patient."}, status=status.HTTP_404_NOT_FOUND)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"supression du dossier médical {num_dossier}")
        

        dossier.delete()
        return Response({"message": "Dossier médical supprimé avec succès."}, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
    
###Get le dossier d'un patient spécifique
class DossiersMedicalByPatientView(generics.ListAPIView):
    serializer_class = DossierMedicalSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request, patient_id):
        """Obtenir les détails d'un dossier médical spécifique."""
        patient = Patient.objects.get(id=patient_id)
        try:
            dossier = DossierMedical.objects.get(patient=patient)
        except DossierMedical.DoesNotExist:
            return Response({"erreur": "Dossier médical introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"récupération du dossier médical du patient {patient.nom} {patient.prenom}")
        
        serializer = DossierMedicalSerializer(dossier)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    

"""
    Partie des visites médicales 
"""

####Vue pour CRUD un patient
class VisitesView(APIView):
    queryset = Visite.objects.all()
    serializer_class = VisiteSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Obtenir le médecin actuellement connecté
        medecin = request.user

        # Récupérer tous les patients associés au médecin
        patients = Patient.objects.filter(medecin=medecin)

        # Filtrer et supprimer les visites médicales passées
        now = make_aware(datetime.now())
        visites_passees = Visite.objects.filter(patient__in=patients, dateRdv__lt=now)
        visites_passees.delete()
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "suppression des visites passées")
        

        # Récupérer les visites restantes
        visites = Visite.objects.filter(patient__in=patients, dateRdv__gte=now)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "recupération des visites")

        # Sérialiser les données
        serializer = VisiteSerializer(visites, many=True)

        # Retourner les données sérialisées
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request):
        """Créer une visite pour un patient spécifique."""
        patient_id = request.data.get("patient")
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"création des visites")
        
        data = request.data.copy()
        data['patient'] = patient_id  # Associer le patient
        serializer = VisiteSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    ##Modification de la visite avec condition date rdv sup à date du jour
    def put(self, request):
        """Modifier un dossier médical d'un patient spécifique."""
        patient_id = request.data.get("patient")
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)

        visite_id = request.data.get("id")
        
        try:
            visite = Visite.objects.get(id=visite_id, patient=patient)
        except Visite.DoesNotExist:
            return Response({"erreur": "Aucune visite programmée pour ce patient."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VisiteSerializer(visite, data=request.data, partial=True)
        if serializer.is_valid():
            today = make_aware(datetime.now())
            if visite.dateRdv <= today + timedelta(hours=24):
                return Response({"erreur": "Le prochain rendez-vous doit être dans plus de 24 heures pour pouvoir être modifié."}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            
            # Enregistrer l'action dans les logs
            self.log_action(request.user, f"modification de la visite du {visite.dateRdv}")
        
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    ##Suppression d'une avec condition date rdv sup à date du jour
    def delete(self, request):
        """Supprimer un patient."""
        visite_id = request.data.get("id")
        if not visite_id:
            return Response({"erreur": "L'identifiant de la visite est requise."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            visite = Visite.objects.get(id=visite_id)
        except Visite.DoesNotExist:
            return Response({"erreur": "Visite introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        today = make_aware(datetime.now())
        if visite.dateRdv <= today + timedelta(hours=24):
            return Response({"erreur": "Le prochain rendez-vous doit être dans plus de 24 heures pour pouvoir être annulée."}, status=status.HTTP_400_BAD_REQUEST)

        visite.delete()
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"suppression de la visite du {visite.dateRdv}")
        
        return Response({"message": "Visite annulée avec succès."}, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    

    
##Get visite en fonction d'une date
class AppointmentByDateView(generics.ListAPIView):
    """
    Récupère toutes les visites médicales programmées pour une date spécifique.
    """
    serializer_class = VisiteSerializer
    permission_classes = [IsAuthenticated]

    
    def get_queryset(self):
        user = self.request.user
        date_visite = self.request.query_params.get('date_visite', None)

        # Vérifier que la date est bien passée en paramètre
        if not date_visite:
            raise ValidationError({"erreur": "Le paramètre 'date_visite' est requis."})

        # Vérifier que la date est au bon format
        try:
            date_obj = datetime.strptime(date_visite, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError({"erreur": "Le format de la date doit être YYYY-MM-DD."})

        # Construire les bornes de la journée
        start_date = make_aware(datetime.combine(date_obj, time.min))
        end_date = make_aware(datetime.combine(date_obj, time.max))

        # Identifier les médecins selon le rôle de l'utilisateur
        if user.role == "admin":
            medecins = User.objects.filter(role="doctor")
        elif user.role == "institution" :
            medecins = User.objects.filter(role="doctor", institution=user)
        elif user.role == "assistant":
            medecins = [user.doctor]
        else:
            medecins = [user]

        # Supprimer les visites passées avant le `now`
        now_dt = now()
        Visite.objects.filter(
            dateRdv__lt=now_dt,
            patient__medecin__in=medecins
        ).delete()

        # Récupérer les visites à la date précisée
        visites = Visite.objects.filter(
            dateRdv__range=(start_date, end_date),
            patient__medecin__in=medecins
        ).select_related('patient')

        # Log l'action
        self.log_action(user, f"a récupéré les visites pour la date {date_visite}")

        return visites

    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
    
    
###Vue pour obtenir les informations d'une visite spéccifique
class GetVisiteDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, visite_id):
        """Obtenir les informations d'un patient spécifique."""
        try:
            visite = Visite.objects.get(id=visite_id)
        except Visite.DoesNotExist:
            return Response({"erreur": "Visite introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        # Enregistrer l'action dans les logs
        self.log_action(request.user, f"récupération des détails de la visite du {visite.dateRdv}")
        
        
        serializer = VisiteSerializer(visite)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    

###Get tous les dossiers 
class AllVisitesView(generics.ListAPIView):
    serializer_class = VisiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Supprimer les visites passées
        self.delete_old_visites()   

        if user.role == "admin":
            queryset = Visite.objects.all()
            self.log_action(user, "récupéré toutes les visites de la base")

        elif user.role == "institution":
            doctors = User.objects.filter(role="doctor", institution=user)
            queryset = Visite.objects.filter(patient__medecin__in=doctors)
            self.log_action(user, "récupéré les visites des médecins qu’il a créés")

        else:
            queryset = Visite.objects.none()

        return queryset

    def list(self, request, *args, **kwargs):
        if self.get_queryset().exists():
            return super().list(request, *args, **kwargs)
        return Response({"erreur": "Accès réservé aux administrateurs et institutions."}, status=status.HTTP_403_FORBIDDEN)

    def log_action(self, user, action):
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
        
    def delete_old_visites(self):
        """Supprimer les visites dont la date est passée."""
        now = make_aware(datetime.now())
        visites_passees = Visite.objects.filter(dateRdv__lt=now)
        visites_passees.delete()
        
