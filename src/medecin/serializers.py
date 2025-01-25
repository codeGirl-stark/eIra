from rest_framework import serializers
from medecin.models import Medecin, PhotoProfil

class MedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medecin
        fields = "__all__"
    
    
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