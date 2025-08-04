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


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AppointmentCreateSerializer
        elif self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        # Optimized queryset with efficient prefetching
        queryset = Appointment.objects.select_related(
            'client', 
            'team_member'
        ).prefetch_related(
            Prefetch('services', queryset=models.QuerySet.model.objects.only('id', 'name', 'price', 'duration_minutes'))
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
        
        # Get existing appointments for the date and team member (optimized query)
        existing_times = set(
            Appointment.objects.filter(
                team_member_id=team_member_id,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'in_progress']
            ).values_list('appointment_time', flat=True)
        )
        
        # Pre-generate all possible slots (more efficient)
        all_slots = [
            f'{hour:02d}:{minute:02d}' 
            for hour in range(9, 18) 
            for minute in [0, 30]
        ]
        
        # Filter out occupied slots
        available_slots = [
            slot for slot in all_slots 
            if datetime.strptime(slot, '%H:%M').time() not in existing_times
        ]
        
        # Cache for 15 minutes
        cache.set(cache_key, available_slots, 900)
        return Response({'available_slots': available_slots})
