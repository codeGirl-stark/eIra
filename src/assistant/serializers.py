from rest_framework import serializers
from .models import Assistant

class AssistantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = ['id', 'user', 'speciality', 'phone_number', 'bio', 'is_active']  # Sélection explicite des champs
