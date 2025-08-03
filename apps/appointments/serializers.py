from rest_framework import serializers
from .models import Appointment
from apps.clients.serializers import ClientSerializer
from apps.services.serializers import ServiceSerializer
from apps.team.serializers import TeamListSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    team_member = TeamListSerializer(read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    total_duration = serializers.SerializerMethodField()
    
    def get_total_duration(self, obj):
        return obj.calculate_total_duration()
    
    class Meta:
        model = Appointment
        fields = ['id', 'client', 'team_member', 'services', 'appointment_date', 'appointment_time', 
                 'status', 'notes', 'total_price', 'total_duration', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']


class AppointmentCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.services.models import Service
        from apps.clients.models import Client
        from apps.team.models import Team
        
        # Override fields with proper querysets
        self.fields['services'] = serializers.PrimaryKeyRelatedField(
            many=True, 
            queryset=Service.objects.filter(is_active=True)
        )
        self.fields['client'] = serializers.PrimaryKeyRelatedField(
            queryset=Client.objects.all()
        )
        self.fields['team_member'] = serializers.PrimaryKeyRelatedField(
            queryset=Team.objects.filter(is_active=True)
        )
    
    def validate(self, data):
        # Check if team member can provide all requested services
        team_member = data.get('team_member')
        services = data.get('services', [])
        
        if team_member and services:
            team_specialties = set(team_member.specialties.values_list('id', flat=True))
            requested_services = set(service.id for service in services)
            
            if not requested_services.issubset(team_specialties):
                raise serializers.ValidationError(
                    "O profissional selecionado não oferece todos os serviços solicitados."
                )
        
        # Check for scheduling conflicts
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        
        if team_member and appointment_date and appointment_time:
            existing = Appointment.objects.filter(
                team_member=team_member,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['scheduled', 'confirmed', 'in_progress']
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing.exists():
                raise serializers.ValidationError(
                    "Este horário já está ocupado para o profissional selecionado."
                )
        
        return data
    
    class Meta:
        model = Appointment
        fields = ['client', 'team_member', 'services', 'appointment_date', 'appointment_time', 'status', 'notes']


class AppointmentListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    team_member_name = serializers.CharField(source='team_member.name', read_only=True)
    services_list = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    
    def get_services_list(self, obj):
        return obj.get_services_list()
    
    def get_total_duration(self, obj):
        return obj.calculate_total_duration()
    
    class Meta:
        model = Appointment
        fields = ['id', 'client_name', 'team_member_name', 'services_list', 'appointment_date', 
                 'appointment_time', 'status', 'total_price', 'total_duration']
