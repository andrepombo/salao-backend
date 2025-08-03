from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.CharField(source='formatted_phone', read_only=True)
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'phone', 'formatted_phone', 'email', 'address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'formatted_phone', 'created_at', 'updated_at']


class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'address']
