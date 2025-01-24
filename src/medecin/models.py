from django.db import models
from admin_app.models import User

# Create your models here.
class Medecin (models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    specialite = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField(verbose_name="Années d'expérience", blank=True, null=True)
    phone_number = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True, default="")

    def __str__(self):
        return f"{self.user.email} - {self.specialite}"
    
    
class PhotoProfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_photo')
    avatar = models.ImageField(upload_to='avatar/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email}"
    
    
class Log (models.Model) :
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(verbose_name= "Date")
    libelle = models.CharField(max_length=255)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)

    
    def __str__(self):
         return f"{self.date} - {self.libelle}"