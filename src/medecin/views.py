import os
import csv
import shutil
from django.apps import apps
from datetime import datetime
from django.db.models import Q
from django.conf import settings
from django.db import connection
from admin_app.models import User
from rest_framework import status
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from admin_app.serializers import DoctorUserSerializer
from dossierMedical.serializers import DossierMedicalSerializer, PatientSerializer
from medecin.models import Medecin, Log, PhotoProfil
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, permissions,viewsets
from dossierMedical.models import Patient, DossierMedical
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from medecin.serializers import MedecinSerializer, PhotoProfilSerializer, LogSerializer



###Vues pour modifier le profile du medecin
class MedecinProfileView(APIView):
    queryset = Medecin.objects.all()
    serializer_class = MedecinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Enregistrer l'action dans les logs
        self.log_action(self.request.user, "erécupération du profil")
        try:
            return Medecin.objects.get(user=self.request.user)
        except Medecin.DoesNotExist:
            raise serializers.ValidationError({"erreur": "Profil non trouvé."})

    def get(self, request):
        # Récupérer les informations du profil du médecin connecté
        profile = self.get_object()
        serializer = MedecinSerializer(profile)
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "récupération du profil")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def post(self, request):
        # Créer un profil pour le médecin connecté
        user = request.user
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "création du profil")
        
        try:
            profile = Medecin.objects.get(user=user)
            return Response({"erreur": "Le profil existe déjà."}, status=status.HTTP_400_BAD_REQUEST)
        except Medecin.DoesNotExist:
            data = request.data.copy()
            data['user'] = user.id  # Associer le profil à l'utilisateur connecté
            serializer = MedecinSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        # Enregistrer l'action dans les logs
        self.log_action(request.user, "modification du profil")
        
        # Modifier le profil du médecin connecté
        profile = self.get_object()
        serializer = MedecinSerializer(profile, data=request.data, partial=True)  # `partial=True` pour les mises à jour partielles
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
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
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
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
 
 ####Exporter la base de données   
class ExportDatabaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request,*args, **kwargs):
        format = request.data.get('format')
        print(f"format : {format}" )
        
        if format == "csv":
            return self.export_to_csv(request)
        elif format == "mysql":
            return self.export_to_mysql(request)
        else:
            return Response({"error": "Format non supporté. Utilisez 'csv', 'mysql'."}, status=400)
      
        
    ##Exporter la base de données sous format csv
    def export_to_csv(self, request):
        csv_filename = "base.csv"

        # Liste de tous les modèles dans l'application
        all_models = apps.get_models()

        # Ouverture du fichier en mode écriture
        with open(csv_filename, 'w', newline='') as csv_file:
            # Création de l'objet writer
            csv_writer = csv.writer(csv_file)

            for model in all_models:
                # Obtention de toutes les instances du modèle
                all_data = model.objects.all()
                
                # Écriture de l'en-tête du CSV (noms de colonnes)
                header = [field.name for field in model._meta.fields]
                csv_writer.writerow([f"{model.__name__} - {col}" for col in header])

                # Écriture des données
                for instance in all_data:
                    csv_writer.writerow([getattr(instance, field) for field in header])

        # Préparer le fichier pour le téléchargement
        with open(csv_filename, 'r') as csv_file:
            response = HttpResponse(csv_file, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{csv_filename}"'
            # response.write(csv_file.read())

        # Enregistrer l'action dans les logs
        self.log_action(request.user, "exporté la base de données sous format CSV")

        # Supprimer le fichier temporaire
        os.remove(csv_filename)

        return response

    ####Exporter la base sous format SQLITE
    """def export_to_sqlite(self, request):
        # Chemin du fichier SQLite actuel
        db_path = settings.DATABASES['default']['NAME']
        
        exported_db_path = os.path.join(settings.BASE_DIR, 'base.sqlite3')

        # Copier le fichier SQLite
        shutil.copy2(db_path, exported_db_path)

        # Préparer le fichier pour le téléchargement
        with open(exported_db_path, 'rb') as db_file:
            response = HttpResponse(db_file, content_type='application/x-sqlite3')
            response['Content-Disposition'] = 'attachment; filename="base.sqlite3"'

        # Enregistrer l'action dans les logs
        self.log_action(request.user, "exporté la base de données sous format SQLite")

        # Supprimer le fichier temporaire
        os.remove(exported_db_path)

        return response"""

    ####Exporter la base sous format mysql
    def export_to_mysql(self, request):
        mysql_dump_path = os.path.join(settings.BASE_DIR, 'base.sql')

        # Commande mysqldump pour exporter la base de données
        db_config = settings.DATABASES['default']
        os.system(
            f"mysqldump -u {db_config['USER']} -p{db_config['PASSWORD']} {db_config['NAME']} > {mysql_dump_path}"
        )

        # Préparer le fichier pour le téléchargement
        with open(mysql_dump_path, 'rb') as dump_file:
            response = HttpResponse(dump_file, content_type='application/sql')
            response['Content-Disposition'] = 'attachment; filename="base.sql"'

        # Enregistrer l'action dans les logs
        self.log_action(request.user, "exporté la base de données sous format MySQL")

        # Supprimer le fichier temporaire
        os.remove(mysql_dump_path)

        return response

    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date = now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )

   
###Importer une base de données 
# class ImportDatabaseAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]

#     def post(self, request, format=None):
#         file = request.FILES.get("file", None)
#         if not file:
#             return Response({"error": "Aucun fichier fourni."}, status=400)

#         # Sauvegarder temporairement le fichier reçu
#         temp_file_path = os.path.join(settings.BASE_DIR, "temp.sql")
#         with open(temp_file_path, "wb") as temp_file:
#             for chunk in file.chunks():
#                 temp_file.write(chunk)

#         # Charger le fichier SQL dans la base de données
#         try:
#             with connection.cursor() as cursor:
#                 with open(temp_file_path, "r") as sql_file:
#                     cursor.execute(sql_file.read())
#         except Exception as e:
#             return Response({"error": f"Erreur lors de l'importation : {str(e)}"}, status=500)
#         finally:
#             os.remove(temp_file_path)

#         # Enregistrer l'action dans les logs
#         self.log_action(request.user, "importé une base de données MySQL")

#         return Response({"success": "Base de données importée avec succès."})

#     def log_action(self, user, action):
#         """Log l'action effectuée."""
#         Log.objects.create(
#             date=now(),
#             libelle=f"{user.username} a {action}.",
#             medecin=get_object_or_404(Medecin, user=user),
#         )


class StatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Fonction générique pour calculer les pourcentages
    def calc_percentage(self, queryset_count, total_count):
        return int((queryset_count / total_count) * 100) if total_count else 0


    def get(self, request, *args, **kwargs):
        medecin = request.user
        
        # Récupération du médecin actif et de ses patients
        patients=Patient.objects.filter(medecin=medecin)
        
        # Récupérer tous les dossiers médicaux du médecin (Optimisé par .prefetch_related)
        dossiers = DossierMedical.objects.filter(patient__medecin=medecin).select_related('patient')
        
        
        total_patients = patients.count()
        
        total_dossiers = dossiers.count()
        
        print(total_patients, total_dossiers)
        
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
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(User, id=user.id),
        )
    
    
class LogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        """Récupérer les logs selon le rôle de l'utilisateur."""
        if request.user.is_admin:
            logs = Log.objects.all()  # L'admin récupère tous les logs
        else:
            logs = Log.objects.filter(medecin=request.user)  # Un médecin ne voit que ses propres logs

        serializer = LogSerializer(logs, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class DeleteLogView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Supprime un log spécifique ou tous les logs selon l'utilisateur."""
        
        log_ids = request.data.getlist("log_ids") or request.data.getlist("log_ids[]") 
        
        if not log_ids:
            return Response({"erreur": "Aucun log sélectionné."}, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(log_ids, str):  # Si reçu sous forme de string, transformer en liste
            log_ids = log_ids.split(',')
        
        # Vérification des droits de suppression
        if request.user.is_admin:
            logs_to_delete = Log.objects.filter(id__in=log_ids)
        else:
            logs_to_delete = Log.objects.filter(id__in=log_ids, medecin=request.user)

        deleted_count, _ = logs_to_delete.delete()
        
        self.log_action(request.user, f"Suppression de {deleted_count} logs")
    
        return Response({"message": f"{deleted_count} logs supprimés."}, status=status.HTTP_200_OK)


    def log_action(self, user, action):
        """Ajoute une entrée dans les logs pour suivre les actions importantes."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} a {action}.",
            medecin=user,
        )


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('q', '')

        if not query:
            return Response({"results": []}, status=200)

        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))
        doctors = Medecin.objects.filter(Q(specialite__icontains=query) | Q(bio__icontains=query))
        patients = Patient.objects.filter(Q(nom__icontains=query) | Q(prenom__icontains=query) | Q(telephone__icontains=query))
        dossiers = DossierMedical.objects.filter(Q(numDossier__icontains=query) | Q(resume__icontains=query))

        results = {
            "users": DoctorUserSerializer(users, many=True).data,
            "doctors": MedecinSerializer(doctors, many=True).data,
            "patients": PatientSerializer(patients, many=True).data,
            "dossiers": DossierMedicalSerializer(dossiers, many=True).data,
        }

        return Response({"results": results}, status=200)