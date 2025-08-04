from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    formatted_phone = serializers.CharField(read_only=True)
    appointments_count = serializers.SerializerMethodField()
    last_appointment = serializers.SerializerMethodField()
    
    def get_appointments_count(self, obj):
        """Get total number of appointments for this client"""
        # Use prefetched data if available to avoid N+1 queries
        if hasattr(obj, '_prefetched_objects_cache') and 'appointments' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['appointments'])
        return obj.appointments.count()
    
    def get_last_appointment(self, obj):
        """Get the date of the last appointment"""
        # Use prefetched data if available
        if hasattr(obj, '_prefetched_objects_cache') and 'appointments' in obj._prefetched_objects_cache:
            appointments = obj._prefetched_objects_cache['appointments']
            if appointments:
                last_apt = max(appointments, key=lambda x: x.appointment_date)
                return last_apt.appointment_date
            return None
        
        last_appointment = obj.appointments.order_by('-appointment_date').first()
        return last_appointment.appointment_date if last_appointment else None
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'phone', 'formatted_phone', 'email', 
            'address', 'birthday', 'gender', 'appointments_count', 
            'last_appointment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'formatted_phone', 'appointments_count', 'last_appointment', 'created_at', 'updated_at']


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
