import os
import csv
import shutil
from django.apps import apps
from datetime import datetime
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
from medecin.models import Medecin, Log, PhotoProfil
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, permissions,viewsets
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from medecin.serializers import MedecinSerializer, PhotoProfilSerializer



###Vues pour modifier le profile du medecin
class MedecinProfileView(APIView):
    queryset = Medecin.objects.all()
    serializer_class = MedecinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        try:
            return Medecin.objects.get(user=self.request.user)
        except Medecin.DoesNotExist:
            raise serializers.ValidationError({"erreur": "Profil non trouvé."})

    def get(self, request):
        # Récupérer les informations du profil du médecin connecté
        profile = self.get_object()
        serializer = MedecinSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        # Créer un profil pour le médecin connecté
        user = request.user
        
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
        # Modifier le profil du médecin connecté
        profile = self.get_object()
        serializer = MedecinSerializer(profile, data=request.data, partial=True)  # `partial=True` pour les mises à jour partielles
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Supprimer le profil du médecin
        profile = self.get_object()
        profile.delete()
        return Response({"message": "Profil supprimé avec succès."}, status=status.HTTP_200_OK)
    
    
#Vue pour enregistrer et récupérer la photo de profil
class PhotoProfileView(viewsets.ModelViewSet):
    queryset = PhotoProfil.objects.all()
    serializer_class = PhotoProfilSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            user = self.request.user
              # L'utilisateur est récupéré à partir du token JWT
            return self.queryset.filter(user=user)
        except (PhotoProfil.DoesNotExist, TokenError):
            return PhotoProfil.objects.none()  # Retourne un queryset vide si l'utilisateur n'est pas trouvé ou le token est invalide

    def perform_create(self, serializer):
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
        # Supprimer la photo de profil
        profile = self.get_object()
        profile.delete()
        return Response({"message": "Profil supprimé avec succès."}, status=status.HTTP_200_OK)
    
    
 
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
class ImportDatabaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        file = request.FILES.get("file", None)
        if not file:
            return Response({"error": "Aucun fichier fourni."}, status=400)

        # Sauvegarder temporairement le fichier reçu
        temp_file_path = os.path.join(settings.BASE_DIR, "temp.sql")
        with open(temp_file_path, "wb") as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        # Charger le fichier SQL dans la base de données
        try:
            with connection.cursor() as cursor:
                with open(temp_file_path, "r") as sql_file:
                    cursor.execute(sql_file.read())
        except Exception as e:
            return Response({"error": f"Erreur lors de l'importation : {str(e)}"}, status=500)
        finally:
            os.remove(temp_file_path)

        # Enregistrer l'action dans les logs
        self.log_action(request.user, "importé une base de données MySQL")

        return Response({"success": "Base de données importée avec succès."})

    def log_action(self, user, action):
        """Log l'action effectuée."""
        Log.objects.create(
            date=now(),
            libelle=f"{user.username} a {action}.",
            medecin=get_object_or_404(Medecin, user=user),
        )