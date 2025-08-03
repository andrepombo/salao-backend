from rest_framework import serializers
from .models import Team
from apps.services.serializers import ServiceSerializer


class TeamSerializer(serializers.ModelSerializer):
    specialties = ServiceSerializer(many=True, read_only=True)
    formatted_phone = serializers.CharField(read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'phone', 'formatted_phone', 'email', 'address', 'specialties', 'hire_date', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'formatted_phone', 'created_at', 'updated_at']


class TeamCreateUpdateSerializer(serializers.ModelSerializer):
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
        
    def validate_phone(self, value):
        """Validate phone number format"""
        if not value.isdigit() or len(value) != 11:
            raise serializers.ValidationError(
                "Phone number must contain exactly 11 digits."
            )
        return value


class TeamListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing team members"""
    specialties_count = serializers.SerializerMethodField()
    formatted_phone = serializers.CharField(read_only=True)
    
    def get_specialties_count(self, obj):
        return obj.specialties.count()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'phone', 'formatted_phone', 'email', 'is_active', 'specialties_count']
