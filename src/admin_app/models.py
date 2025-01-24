from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


# Custom User Model
class User(AbstractUser):
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_doctor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'  # Utilisation de l'email pour l'authentification
    REQUIRED_FIELDS = ['username']  # Pas de champs obligatoires en dehors de l'email

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.is_admin:
            self.is_staff = True
        super().save(*args, **kwargs)