from rest_framework import serializers
from .models import Team
from apps.services.serializers import ServiceSerializer


class TeamSerializer(serializers.ModelSerializer):
    specialties = ServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'phone', 'email', 'address', 'specialties', 'hire_date', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeamCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.services.models import Service
        # Override the specialties field with proper queryset
        self.fields['specialties'] = serializers.PrimaryKeyRelatedField(
            many=True, 
            queryset=Service.objects.filter(is_active=True)
        )
    
    class Meta:
        model = Team
        fields = ['name', 'phone', 'email', 'address', 'specialties', 'hire_date', 'is_active']


class TeamListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing team members"""
    specialties_count = serializers.SerializerMethodField()
    
    def get_specialties_count(self, obj):
        return obj.specialties.count()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'phone', 'email', 'is_active', 'specialties_count']
