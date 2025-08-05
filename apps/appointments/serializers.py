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
        from datetime import datetime, timedelta

        team_member = data.get('team_member')
        services = data.get('services', [])
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        instance_id = self.instance.id if self.instance else None

        # 1. Check if team member can provide all requested services
        if team_member and services:
            team_specialties = set(team_member.specialties.values_list('id', flat=True))
            requested_services_ids = {service.id for service in services}
            if not requested_services_ids.issubset(team_specialties):
                raise serializers.ValidationError(
                    "O profissional selecionado não oferece todos os serviços solicitados."
                )

        # 2. Check for scheduling conflicts, considering duration
        if team_member and appointment_date and appointment_time and services:
            # Calculate new appointment's start and end datetimes
            new_duration = sum(service.duration_minutes for service in services)
            if new_duration <= 0:
                return data # No duration, no conflict

            new_start_dt = datetime.combine(appointment_date, appointment_time)
            new_end_dt = new_start_dt + timedelta(minutes=new_duration)

            # Fetch potentially conflicting appointments
            conflicts = Appointment.objects.filter(
                team_member=team_member,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'in_progress']
            ).exclude(id=instance_id)

            for existing_app in conflicts:
                # Calculate existing appointment's start and end datetimes
                existing_duration = existing_app.calculate_total_duration()
                if existing_duration <= 0:
                    continue
                
                existing_start_dt = datetime.combine(existing_app.appointment_date, existing_app.appointment_time)
                existing_end_dt = existing_start_dt + timedelta(minutes=existing_duration)

                # The overlap condition: (StartA < EndB) and (EndA > StartB)
                if new_start_dt < existing_end_dt and new_end_dt > existing_start_dt:
                    raise serializers.ValidationError(
                        f"Conflito de agendamento. O profissional já tem um compromisso das "
                        f"{existing_start_dt.strftime('%H:%M')} às {existing_end_dt.strftime('%H:%M')}."
                    )

        return data
    
    def update(self, instance, validated_data):
        print(f'🔄 AppointmentCreateSerializer.update() called')
        print(f'📋 Instance ID: {instance.id}')
        print(f'📋 Validated data received: {validated_data}')
        
        # Extract services from validated_data since it's a many-to-many field
        services = validated_data.pop('services', None)
        print(f'📋 Services to update: {services}')
        
        # Log current services before update
        current_services = list(instance.services.values_list('id', flat=True))
        print(f'📋 Current services before update: {current_services}')
        
        # Update all other fields normally
        for attr, value in validated_data.items():
            print(f'📋 Setting {attr} = {value}')
            setattr(instance, attr, value)
        
        # Save the instance first
        instance.save()
        print(f'✅ Instance saved with regular fields')
        
        # Update the many-to-many services field
        if services is not None:
            print(f'🔄 Updating services from {current_services} to {[s.id for s in services]}')
            instance.services.set(services)
            
            # Recalculate total price after updating services
            old_price = instance.total_price
            instance.total_price = instance.calculate_total_price()
            print(f'💰 Price updated from {old_price} to {instance.total_price}')
            instance.save(update_fields=['total_price'])
        
        # Log final state
        final_services = list(instance.services.values_list('id', flat=True))
        print(f'✅ Final services after update: {final_services}')
        print(f'✅ Final total price: {instance.total_price}')
        
        return instance
    
    class Meta:
        model = Appointment
        fields = ['client', 'team_member', 'services', 'appointment_date', 'appointment_time', 'status', 'notes']


class AppointmentListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    team_member_name = serializers.CharField(source='team_member.name', read_only=True)
    services_list = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    
    def get_services_list(self, obj):
        # Optimized: Use prefetched services to avoid additional queries
        if hasattr(obj, '_prefetched_objects_cache') and 'services' in obj._prefetched_objects_cache:
            return ", ".join([service.name for service in obj._prefetched_objects_cache['services']])
        return obj.get_services_list()
    
    def get_total_duration(self, obj):
        # Optimized: Use prefetched services to avoid additional queries
        if hasattr(obj, '_prefetched_objects_cache') and 'services' in obj._prefetched_objects_cache:
            return sum(service.duration_minutes for service in obj._prefetched_objects_cache['services'])
        return obj.calculate_total_duration()
    
    class Meta:
        model = Appointment
        fields = ['id', 'client_name', 'team_member_name', 'services_list', 'appointment_date', 
                 'appointment_time', 'status', 'total_price', 'total_duration']
