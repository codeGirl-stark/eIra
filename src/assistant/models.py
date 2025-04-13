from django.db import models
from admin_app.models import User
from medecin.models import Medecin


class Assistant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='assistant_profile')
    speciality = models.CharField(max_length=100, verbose_name="Spécialité d'assistance", blank=True, null=True)
    phone_number = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    bio = models.TextField(blank=True, null=True, default="")
    is_active = models.BooleanField(default=True, verbose_name="Statut actif")

    def __str__(self):
        return f"{self.user.email}"
