from rest_framework import serializers
from admin_app.models import User, UserRole, PhotoProfil
from django.contrib.auth.hashers import make_password
from django.core.validators import EmailValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Serializer pour la création d'un administrateur
class AdminUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'is_active']
        read_only_fields = ['email', 'role']
        extra_kwargs = {'password': {'write_only': True}}
        
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)

        if not password:
            raise serializers.ValidationError({"password": "Le mot de passe est requis."})
        
        validated_data['password'] = password
        validated_data['role'] = UserRole.ADMIN
        validated_data['is_active'] = True
        return User.objects.create_superuser(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            try:
                validate_password(password, instance)
            except ValidationError as e:
                raise serializers.ValidationError({"password": e.messages})
            instance.set_password(password)

        instance.save()
        return instance
    
    
# Serializer pour la création d'une institution
class InstitutionUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'is_active']
        read_only_fields = ['role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        if not password:
            raise serializers.ValidationError({"password": "Le mot de passe est requis."})
        
        validated_data['password'] = password
        validated_data['role'] = UserRole.INSTITUTION
        validated_data['is_active'] = True
        return User.objects.create_institution(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Utiliser set_password pour hacher le mot de passe
        instance.save()
        return instance
    
    
# Serializer pour la création d'un médecin
class DoctorUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")])
    
    institution = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.INSTITUTION), write_only=True
    )
    institution_username = serializers.CharField(source='institution.username', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'institution', 'institution_username', 'is_active']
        read_only_fields = ['role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        if not password:
            raise serializers.ValidationError({"password": "Le mot de passe est requis."})
        
        validated_data['password'] = password
        validated_data['role'] = UserRole.DOCTOR
        validated_data['is_active'] = True
        return User.objects.create_doctor(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Utiliser set_password pour hacher le mot de passe
        instance.save()
        return instance
    
    
# Serializer pour la création d'un assistant
class AssistantUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator(message="L'adresse e-mail doit être au format valide.")])
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.DOCTOR), write_only=True
    )
    doctor_email = serializers.CharField(source='doctor.email', read_only=True)
    institution = serializers.CharField(source='doctor.institution.username', read_only=True)  # Récupérer l'institution du médecin

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'doctor', 'doctor_email', 'institution', 'is_active']
        read_only_fields = ['role','doctor_email']
        extra_kwargs = {'password': {'write_only': True}}
        
    def get_doctor_email(self, obj):
        if obj.email:
            return obj.email  # Assure-toi que `medecin` est bien lié au modèle User
        return None

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        if not password:
            raise serializers.ValidationError({"password": "Le mot de passe est requis."})
        
        validated_data['password'] = password
        validated_data['role'] = UserRole.ASSISTANT
        validated_data['is_active'] = True
        return User.objects.create_assistant(**validated_data)
    
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


class PhotoProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoProfil
        fields = ['id', 'avatar', 'user']  # Inclure uniquement les champs nécessaires
        read_only_fields = ['user']  # Rendre le champ user en lecture seule
        
    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.user_id = validated_data.get('user_id', instance.user_id)
        instance.save()
        return instance
        
    def clean_profile_picture(self):
        file = self.cleaned_data.get('avatar')
        if file:
            if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.PNG','.JPG', '.JPEG', )):
                raise serializers.ValidationError("Le fichier doit être soit une image soit un pdf.")
            if file.size > 2 * 1024 * 1024:  # 2 MB max
                raise serializers.ValidationError("La taille du fichier est trop large.")
        return file
