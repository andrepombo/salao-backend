from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.CharField(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'phone', 'formatted_phone', 'email', 
            'address', 'birthday', 'gender', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'formatted_phone', 'created_at', 'updated_at']


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'address', 'birthday', 'gender']
        
    def validate_phone(self, value):
        """Validate phone number format"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError(
                "Phone number must contain exactly 11 digits."
            )
        return value
