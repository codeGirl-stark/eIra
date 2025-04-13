from rest_framework import serializers
from medecin.models import Medecin, Log


class MedecinSerializer(serializers.ModelSerializer): 
    class Meta:
        model = Medecin
        fields = ['id', 'user', 'specialite', 'years_of_experience', 'phone_number', 'bio']

    
class LogSerializer(serializers.ModelSerializer):
    medecin_email = serializers.EmailField(source='medecin.email', read_only=True)

    class Meta:
        model = Log
        fields = ['id', 'date', 'libelle', 'medecin_email']
        
    
