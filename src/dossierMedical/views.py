from django.shortcuts import render
from rest_framework import status
from admin_app.models import User
from rest_framework import generics
from datetime import date, timedelta
from dossierMedical import serializers
from rest_framework.views import APIView
from datetime import datetime, timedelta
from .models import DossierMedical,Patient, Visite
from django.utils.timezone import make_aware
from rest_framework.response import Response
from django.db.models.functions import TruncDate
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import DossierMedicalSerializer, PatientSerializer,VisiteSerializer


####Vue pour CRUD un patient
class PatientView(APIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Créer un patient pour le médecin connecté."""
        if not request.user.is_doctor:
            return Response({"erreur": "Seuls les médecins peuvent créer des patients."}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data.copy()
        data['medecin'] = request.user.id
        
        serializer = PatientSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        """Obtenir les patients associés au médecin connecté."""
        if not request.user.is_doctor:
            return Response({"erreur": "Seuls les médecins peuvent consulter leurs patients."}, status=status.HTTP_403_FORBIDDEN)

        patients = Patient.objects.filter(medecin=request.user)
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def put(self, request):
        """Modifier un patient existant."""
        patient_id = request.data.get("id")
        if not patient_id:
            return Response({"erreur": "L'identifiant du patient est requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id, medecin=request.user)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)
        
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
        
        patient.delete()
        return Response({"message": "Patient supprimé avec succès."}, status=status.HTTP_200_OK)
    

###Vue pour obtenir les informations d'un patient spécifique
class GetPatientDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        """Obtenir les informations d'un patient spécifique."""
        try:
            patient = Patient.objects.get(id=patient_id, medecin=request.user)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable ou non associé au médecin connecté."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PatientSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)


##Vue pour récupérer tous les patients
class GetAllPatients(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtenir tous les patients (admin uniquement)."""
        if not request.user.is_admin:
            return Response({"erreur": "Accès réservé aux administrateurs."}, status=status.HTTP_403_FORBIDDEN)
        
        patients = Patient.objects.all()
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
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

        dossier.delete()
        return Response({"message": "Dossier médical supprimé avec succès."}, status=status.HTTP_200_OK)
    
    
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

        serializer = DossierMedicalSerializer(dossier)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
  
###Get tous les dossiers    
class AllDossiersMedicalView(generics.ListAPIView):
    serializer_class = DossierMedicalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Récupère tous les dossiers médicaux dans la base de données."""
        return DossierMedical.objects.all()  # Aucun filtre, récupère tous les dossiers
    

#####Partie des visites médicales 

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

        # Récupérer toutes les visites médicales des patients du médecin
        visites = Visite.objects.filter(patient__in=patients)

        # Sérialiser les données
        serializer = VisiteSerializer(visites, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request):
        """Créer une visite pour un patient spécifique."""
        patient_id = request.data.get("patient")
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Patient introuvable."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response({"message": "Visite annulée avec succès."}, status=status.HTTP_200_OK)

    
##Get visite en fonction d'une date
class VisitesByDateView(generics.ListAPIView):
    """
    Récupère toutes les visites médicales programmées pour une date spécifique.
    """
    serializer_class = VisiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        medecin = self.request.user
        
        date_visite = self.request.query_params.get('date_visite', None)
        if not date_visite:
            return Response({"erreur": "Aucune visite prévue."}, status=status.HTTP_404_NOT_FOUND)

        try:
            date_obj = datetime.strptime(date_visite, "%Y-%m-%d").date()
        except ValueError:
            return Response({"erreur": "Le format de la date doit être YYYY-MM-DD."}, status=status.HTTP_404_NOT_FOUND)

        # Filtrer les visites par date sans tenir compte de l'heure
        start_date = make_aware(datetime.combine(date_obj, datetime.min.time()))
        end_date = make_aware(datetime.combine(date_obj, datetime.max.time()))
        
        # Retourner les visites médicales correspondant à la date
        queryset = Visite.objects.annotate(
            date_only=TruncDate('dateRdv')
        ).filter(
            dateRdv__gte=start_date, 
            dateRdv__lt=end_date,
            patient__medecin=medecin.id
        ).select_related('patient') 
        
        # Supprimer les visites passées par rapport à la date et l'heure actuelles
        now = make_aware(datetime.now())
        for visite in queryset:
            if visite.dateRdv < now:
                visite.delete()
        return queryset
    
    
###Vue pour obtenir les informations d'une visite spéccifique
class GetVisiteDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, visite_id):
        """Obtenir les informations d'un patient spécifique."""
        try:
            visite = Visite.objects.get(id=visite_id)
        except Patient.DoesNotExist:
            return Response({"erreur": "Visite introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VisiteSerializer(visite)
        return Response(serializer.data, status=status.HTTP_200_OK)
