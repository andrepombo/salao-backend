from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentCreateSerializer, AppointmentListSerializer
from apps.services.models import Service


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AppointmentCreateSerializer
        elif self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer
        
    def list(self, request, *args, **kwargs):
        """
        Override list method to add caching for the main appointments list
        Cache key is based on query parameters to ensure different filtered views have separate caches
        """
        # Create a cache key based on the query parameters
        query_params = request.query_params.urlencode()
        cache_key = f'appointments_list_{query_params}'
        
        # Also set a master key for cache invalidation
        master_key = 'appointments_list_all'
        
        # Try to get from cache first
        if cache.get(master_key) is None:
            # If master key is missing, don't use any cached data
            cached_data = None
        else:
            cached_data = cache.get(cache_key)
            
        if cached_data is not None:
            return Response(cached_data)
            
        # If not in cache, proceed with normal list retrieval
        response = super().list(request, *args, **kwargs)
        
        # Cache for 2 minutes (adjust based on how frequently your data changes)
        cache.set(cache_key, response.data, 120)
        
        # Set or refresh the master key
        cache.set(master_key, True, 120)
        
        return response
    
    def get_queryset(self):
        # Optimized queryset with efficient prefetching
        queryset = Appointment.objects.select_related(
            'client', 
            'team_member'
        ).prefetch_related(
            Prefetch('services', queryset=Service.objects.only('id', 'name', 'price', 'duration_minutes'))
        )
        
        # Build filters efficiently
        filters = Q()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            filters &= Q(appointment_date__gte=start_date)
        if end_date:
            filters &= Q(appointment_date__lte=end_date)
            
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            filters &= Q(status=status_filter)
            
        # Filter by team member
        team_member = self.request.query_params.get('team_member')
        if team_member:
            filters &= Q(team_member_id=team_member)
        
        # Apply all filters at once
        if filters:
            queryset = queryset.filter(filters)
            
        return queryset.order_by('appointment_date', 'appointment_time')
    
    def perform_create(self, serializer):
        appointment = serializer.save()
        # Calculate total price after saving (needed for M2M relationships)
        if appointment.services.exists():
            appointment.total_price = appointment.calculate_total_price()
            appointment.save(update_fields=['total_price'])
        
        # Invalidate relevant caches when a new appointment is created
        self._invalidate_appointment_caches(appointment)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments - optimized with caching"""
        today = timezone.now().date()
        cache_key = f'appointments_today_{today}'
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # If not in cache, query database
        appointments = self.get_queryset().filter(appointment_date=today)
        serializer = AppointmentListSerializer(appointments, many=True)
        
        # Cache for 5 minutes
        cache.set(cache_key, serializer.data, 300)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments (next 7 days) - optimized with caching"""
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        cache_key = f'appointments_upcoming_{today}_{next_week}'
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # If not in cache, query database
        appointments = self.get_queryset().filter(
            appointment_date__range=[today, next_week],
            status__in=['scheduled', 'confirmed']
        )
        serializer = AppointmentListSerializer(appointments, many=True)
        
        # Cache for 10 minutes
        cache.set(cache_key, serializer.data, 600)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update appointment status"""
        appointment = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.save(update_fields=['status'])
            
            # Invalidate caches when status changes
            self._invalidate_appointment_caches(appointment)
            
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Status inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def available_slots(self, request):
        """Get available time slots for a specific date and team member - optimized"""
        date = request.query_params.get('date')
        team_member_id = request.query_params.get('team_member')
        
        if not date or not team_member_id:
            return Response(
                {'error': 'Data e profissional são obrigatórios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cache key for available slots
        cache_key = f'available_slots_{team_member_id}_{date}'
        cached_slots = cache.get(cache_key)
        if cached_slots is not None:
            return Response({'available_slots': cached_slots})
        
        # Get existing appointments to calculate occupied slots including duration
        existing_appointments = Appointment.objects.filter(
            team_member_id=team_member_id,
            appointment_date=appointment_date,
            status__in=['scheduled', 'confirmed', 'in_progress']
        ).prefetch_related('services')

        occupied_slots = set()
        for app in existing_appointments:
            start_time = app.appointment_time
            duration = app.calculate_total_duration()
            if duration > 0:
                # Combine date and time for accurate calculations
                start_datetime = datetime.combine(appointment_date, start_time)
                end_datetime = start_datetime + timedelta(minutes=duration)

                # Add all 30-minute intervals covered by the appointment to occupied_slots
                current_slot_time = start_datetime
                while current_slot_time < end_datetime:
                    occupied_slots.add(current_slot_time.time())
                    current_slot_time += timedelta(minutes=30)

        # Pre-generate all possible slots
        all_slots = [
            f'{hour:02d}:{minute:02d}'
            for hour in range(7, 21)  # Hours from 07:00 to 20:xx
            for minute in [0, 30]
        ]

        # Filter out occupied slots
        available_slots = [
            slot for slot in all_slots
            if datetime.strptime(slot, '%H:%M').time() not in occupied_slots
        ]
        
        # Cache for 15 minutes
        cache.set(cache_key, available_slots, 900)
        return Response({'available_slots': available_slots})
        
    def update(self, request, *args, **kwargs):
        """Override update to invalidate caches"""
        response = super().update(request, *args, **kwargs)
        self._invalidate_appointment_caches(self.get_object())
        return response
        
    def destroy(self, request, *args, **kwargs):
        """Override destroy to invalidate caches"""
        appointment = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        self._invalidate_appointment_caches(appointment)
        return response
        
    def _invalidate_appointment_caches(self, appointment):
        """Helper method to invalidate relevant caches when an appointment changes"""
        # Clear today cache if the appointment is for today
        today = timezone.now().date()
        if appointment.appointment_date == today:
            cache.delete(f'appointments_today_{today}')
            
        # Clear upcoming cache if appointment is in the next 7 days
        next_week = today + timedelta(days=7)
        if today <= appointment.appointment_date <= next_week:
            cache.delete(f'appointments_upcoming_{today}_{next_week}')
            
        # Clear available slots cache for this team member and date
        cache.delete(f'available_slots_{appointment.team_member_id}_{appointment.appointment_date}')
        
        # Clear list caches - using a simple approach that works with all cache backends
        # In a production environment with many users, you might want a more targeted approach
        # For now, we'll just invalidate all list caches with a single key
        cache.delete('appointments_list_all')
