from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'service_type', 'description', 'duration_minutes', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'service_type', 'description', 'duration_minutes', 'price', 'is_active']
        
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )
        return value
        
    def validate_duration_minutes(self, value):
        """Validate duration is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "Duration must be greater than zero minutes."
            )
        return value
