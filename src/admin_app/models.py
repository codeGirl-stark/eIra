from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Rôles possibles
class UserRole(models.TextChoices):
    ADMIN = "admin", "Administrateur"
    INSTITUTION = "institution", "Institution"
    DOCTOR = "doctor", "Médecin"
    ASSISTANT = "assistant", "Assistant"
  
    
# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def create_institution(self, email, password, **extra_fields):
        extra_fields.setdefault('role', UserRole.INSTITUTION)
        return self.create_user(email, password, **extra_fields)

    def create_doctor(self, email, password, institution, **extra_fields):
        if not institution:
            raise ValueError("Un médecin doit être affilié à une institution")
        extra_fields.setdefault('role', UserRole.DOCTOR)
        extra_fields.setdefault('institution', institution)
        return self.create_user(email, password, **extra_fields)

    def create_assistant(self, email, password, doctor, **extra_fields):
        if not doctor:
            raise ValueError("Un assistant doit être affilié à un médecin")
        extra_fields.setdefault('role', UserRole.ASSISTANT)
        extra_fields.setdefault('doctor', doctor)
        return self.create_user(email, password, **extra_fields)


# Custom User Model
class User(AbstractUser):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.DOCTOR)

    institution = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="institutions")
    doctor = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="assistants")
   
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'  # Utilisation de l'email pour l'authentification
    REQUIRED_FIELDS = ['username']  # Pas de champs obligatoires en dehors de l'email

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    

class PhotoProfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_photo')
    avatar = models.ImageField(upload_to='avatar/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email}"
    
        
        
class UserVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="visits")
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.email} - {self.timestamp}"
    
