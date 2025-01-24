from rest_framework import serializers
from datetime import date
from .models import DossierMedical, Patient, Visite

###Sérializer pour la table Patient
class PatientSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Patient
        fields = '__all__'
        
    # Champ supplémentaire pour l'année de naissance
    annee_naissance = serializers.IntegerField(write_only=True, required=True)

    def validate(self, data):
        # Calculer l'âge à partir de l'année de naissance
        if 'annee_naissance' in data:
            current_year = date.today().year
            age = current_year - data['annee_naissance']
            if age < 0 or age > 150:  # Vérification simple pour éviter les incohérences
                raise serializers.ValidationError("L'année de naissance est invalide.")
            data['age'] = age
            del data['annee_naissance']  # Supprimer l'année de naissance après utilisation

        return data
        

####Serializer de la table Visite
class VisiteSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    patientInfo = PatientSerializer(source='patient', read_only=True)  # Pour l'affichage des infos du patient
    
    class Meta:
        model = Visite
        fields = '__all__'  # Inclure tous les champs ou préciser ceux nécessaires


####Serializer de la table Dossier médical
class DossierMedicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierMedical
        fields = '__all__'  # Inclure tous les champs ou préciser ceux nécessaires

    