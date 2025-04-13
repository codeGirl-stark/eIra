from.models import Assistant
from django.db.models import Q
from medecin.models import Log
from rest_framework import status
from admin_app.models import User
from rest_framework import viewsets
from rest_framework import generics
from django.utils.timezone import now
from rest_framework.views import APIView
from django.utils.timezone import make_aware
from rest_framework.response import Response
from .serializers import AssistantSerializer
from medecin.serializers import LogSerializer
from datetime import datetime, timedelta, time
from rest_framework.generics import ListAPIView
from django.db.models.functions import TruncDate
from admin_app.permissions import IsAssistantOfDoctor
from django.shortcuts import get_object_or_404, render
from admin_app.serializers import DoctorUserSerializer
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from dossierMedical.models import Patient, Visite, DossierMedical
from dossierMedical.serializers import PatientSerializer, VisiteSerializer


# Vues Pour modifier le profil de l'assistant
class AssistantProfileView(APIView):
    queryset = Assistant.objects.all()
    serializer_class = AssistantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Récupère le profil du médecin connecté."""
        try:
            assistant = Assistant.objects.get(user=self.request.user)
            self.log_action(self.request.user, "récupération du profil médecin")
            return assistant
        except Assistant.DoesNotExist:
            raise NotFound({"erreur": "Profil non existant."})  # Utilisation de NotFound pour une meilleure gestion d'erreur


    def get(self, request):
        # Récupérer les informations du profil du médecin connecté
        profile = self.get_object()
        serializer = AssistantSerializer(profile)
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "récupération du profil")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        # Créer un profil pour le médecin connecté
        user = request.user
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "création du profil")
        
        try:
            profile = Assistant.objects.get(user=user)
            return Response({"erreur": "Le profil existe déjà."}, status=status.HTTP_400_BAD_REQUEST)
        except Assistant.DoesNotExist:
            data = request.data.copy()
            data['user'] = user.id  # Associer le profil à l'utilisateur connecté
            serializer = AssistantSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "modification du profil")
        
        # Modifier le profil du médecin connecté
        profile = self.get_object()
        serializer = AssistantSerializer(profile, data=request.data, partial=True)  # `partial=True` pour les mises à jour partielles
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "suppression du profil")
        
        # Supprimer le profil du médecin
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



class PatientViewSet(ListAPIView):
    """
    Permet aux assistants de voir uniquement les patients du médecin auquel ils sont affiliés.
    """
    serializer_class = PatientSerializer
    permission_classes = [IsAssistantOfDoctor]

    def get_queryset(self):
        patient = Patient.objects.filter(medecin=self.request.user.doctor)
        return patient 
    
####Get doctor username for assistant   
class GetDocteurPseudoView(ListAPIView):
    serializer_class = DoctorUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer l'utilisateur du médecin
            medecin = User.objects.get(id=request.user.doctor_id)  
            
            # Retourner son pseudo (username)
            return Response({"username": medecin.username}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "Médecin introuvable"}, status=status.HTTP_404_NOT_FOUND) 


class VisitesView(viewsets.ModelViewSet):
    """
    Permet aux assistants de gérer les rendez-vous des patients du médecin.
    """
    serializer_class = VisiteSerializer
    permission_classes = [IsAssistantOfDoctor]

    def get_queryset(self):
        return Visite.objects.filter(patient__doctor=self.request.user.doctor)

    def perform_create(self, serializer):
        # Empêcher la création de rendez-vous pour un autre médecin
        if serializer.validated_data['patient'].doctor != self.request.user.doctor:
            return Response({"erreur": "Vous ne pouvez gérer que les patients de votre médecin affilié."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()
        
        
class AppointmentViewSet(APIView):
    queryset = Visite.objects.all()
    serializer_class = VisiteSerializer
    permission_classes = [IsAssistantOfDoctor]

    def get(self, request):
        # Obtenir le médecin actuellement connecté
        medecin = request.user.doctor

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
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
class StatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Fonction générique pour calculer les pourcentages
    def calc_percentage(self, queryset_count, total_count):
        return int((queryset_count / total_count) * 100) if total_count else 0


    def get(self, request, *args, **kwargs):
        medecin = request.user.doctor
        
        # Récupération du médecin actif et de ses patients
        patients=Patient.objects.filter(medecin=medecin)
        
        # Récupérer tous les dossiers médicaux du médecin (Optimisé par .prefetch_related)
        dossiers = DossierMedical.objects.filter(patient__medecin=medecin).select_related('patient')
        
        total_assistants = User.objects.filter(doctor = medecin).count()
        
        total_patients = patients.count()
        
        total_dossiers = dossiers.count()
        
        ##print(total_patients, total_dossiers)
        
        if total_patients == 0:
            return Response({"message": "Aucun patient trouvé pour ce médecin"}, status=status.HTTP_400_BAD_REQUEST)

        if total_dossiers == 0:
            return Response({"message": "Aucun dossier enregistré"}, status=status.HTTP_400_BAD_REQUEST)


        # Définir les intervalles pour les catégories
        agedecouverte_ranges = {
            'agedecouverte1': (0, 24),
            'agedecouverte2': (25, 50),
            'agedecouverte3': (50, 80),
            'agedecouverte4': (80, 100),
            'agedecouverte5': (100, 300),
        }

        cumul_ranges = {
            'cumul1': (0, 9),
            'cumul2': (10, 29),
            'cumul3': (30, 49),
            'cumul4': (50, 100),
            'cumul5': (100, 5000)
        }
        
        categories_patient = {
            'homme': Q(sexe='M'),
            'femme': Q(sexe='F'),
            
            'ado': Q(age__lt=40),
            'jeune': Q(age__gte=40, age__lt=60),
            'adulte': Q(age__gte=60),
        }

         # Définir les filtres
        categories = {
            'carcinome': Q(carcinomeFamiliale=True),
            'effra': Q(effraCapsulaire=True),
            'embon': Q(embonVasculaire=True),
            'refrac': Q(refrac__isnull=False),  # Si refrac a une valeur, on considère qu'il est utilisé
        }


        # Calcul des statistiques par catégorie
        stats = {}
        # Ajouter les totaux et les pourcentages des assistants
        stats['total_assistants'] = {
            'count': total_assistants,
            'percentage': self.calc_percentage(total_assistants, total_assistants)  # 100% pour les patients
        }
        
        # Ajouter les totaux et les pourcentages des patients et dossiers
        stats['total_patients'] = {
            'count': total_patients,
            'percentage': self.calc_percentage(total_patients, total_patients)  # 100% pour les patients
        }

        stats['total_dossiers'] = {
            'count': total_dossiers,
            'percentage': self.calc_percentage(total_dossiers, total_dossiers)  # 100% pour les dossiers
        }
        
        for category_patient, filter_query in categories_patient.items():
            count = patients.filter(filter_query).count()
            stats[category_patient] = {
                'count': count,
                'percentage': self.calc_percentage(count, total_patients)
            }
            
        for category, filter_query in categories.items():
            count = dossiers.filter(filter_query).count()
            stats[category] = {
                'count': count,
                'percentage': self.calc_percentage(count, total_dossiers)
            }
            
        # Fonction pour traiter les champs avec des valeurs multiples
        def process_field(field_name, values, is_range=False):
            for key, value in values.items() if is_range else enumerate(values):
                if is_range:  # Si les valeurs sont des intervalles
                    min_value, max_value = value
                    count = dossiers.filter(**{f"{field_name}__range": (min_value, max_value)}).count()
                else:  # Si les valeurs sont des catégories simples
                    count = dossiers.filter(**{f"{field_name}": value}).count()

                stats[f"{field_name}_{key}"] = {
                    'count': count,
                    'percentage': self.calc_percentage(count, total_patients),
                }
                
        # Appliquer les calculs à chaque champ supplémentaire (âge à la découverte, type histologique, etc.)
        fields_to_filter = {
            'ageDecouverte': agedecouverte_ranges,
            'typeHisto': ['Papillaire', 'Vesiculaire', 'PapilloVesiculaire', 'Medullaire', 'Anaplasique', 'Autres'],
            'clasT': ['Tx', 'T0', 'T1a', 'T1b', 'T2', 'T3a', 'T3b', 'T4a', 'T4b'],
            'clasN': ['Nx', 'N0', 'N1a', 'N1b'],
            'clasM': ['Mx', 'M0', 'M1'],
            'stade': ['I', 'II', 'III', 'IVA', 'IVB'],
            'risque': ['Faible', 'Intermediaire', 'Haut'],
        }
        
        for field_name, values in fields_to_filter.items():
            process_field(field_name, values, is_range=field_name == "ageDecouverte")

        # Appliquer les calculs pour les intervalles de cures et de cumul
        for field_name, ranges in {'activiteCumule': cumul_ranges}.items():
            process_field(field_name, ranges, is_range=True)
            
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "récupération des informations statistiques")

        return Response(stats, status=status.HTTP_200_OK)
    
    
    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    