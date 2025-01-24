from django.shortcuts import render
from admin_app.models import User
from rest_framework import status
from rest_framework import serializers
from rest_framework.views import APIView
from .permissions import IsActivePermission
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from admin_app.serializers import AdminUserSerializer, DoctorUserSerializer, LoginSerializer

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
            serializer = self.serializer_class(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"erreur": "Médecin non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    


