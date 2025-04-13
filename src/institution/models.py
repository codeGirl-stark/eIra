from django.db import models
from admin_app.models import User

# Create your models here.

class Institution(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution_profile')
    address = models.TextField(verbose_name="Adresse")
    phone_number = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    institution_type = models.CharField(max_length=100, verbose_name="Type d'institution")
    responsable = models.CharField(max_length=255, verbose_name="Responsable")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def __str__(self):
        return f"{self.user.username} - {self.institution_type}"
