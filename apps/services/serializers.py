from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'service_type', 'description', 'duration_minutes', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'service_type', 'description', 'duration_minutes', 'price', 'is_active']
