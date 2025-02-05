from rest_framework import serializers
from admin_app.models import User
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken



###Serializer pour création de l'admin
class AdminUserSerializer(serializers.ModelSerializer):
    #Validation de l'adresse mail
    email = serializers.EmailField(
        validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")]
    )
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_admin', 'is_active']
        read_only_fields = ['email']  # Empêche la modification de l'email
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_admin'] = True
        validated_data['is_active'] = True
        return User.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Utiliser set_password pour hacher le mot de passe
        instance.save()
        return instance

    
##Serializers pour création du medecin
class DoctorUserSerializer(serializers.ModelSerializer):
    #Validation de l'adresse mail
    email = serializers.EmailField(
        validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")]
    )
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'is_doctor', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_doctor'] = True
        validated_data['is_active'] = True
        return User.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Utiliser set_password pour hacher le mot de passe
        instance.save()
        return instance
 
   
##Sérializer pour connexion
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError(_("Vous devez fournir une adresse e-mail et un mot de passe."))

        # Authentification basée sur email
        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError(_("Email ou mot de passe incorrect."))

        if not user.is_active:
            raise serializers.ValidationError(_("Ce compte utilisateur est désactivé. Veuillez contacter l'administrateur."))

        attrs['user'] = user
        return attrs


