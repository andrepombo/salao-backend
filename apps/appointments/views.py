from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.utils import timezone
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
        queryset = Appointment.objects.select_related('client', 'team_member').prefetch_related('services')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
            
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by team member
        team_member = self.request.query_params.get('team_member')
        if team_member:
            queryset = queryset.filter(team_member_id=team_member)
            
        return queryset.order_by('appointment_date', 'appointment_time')
    
    def perform_create(self, serializer):
        appointment = serializer.save()
        # Calculate total price after saving (needed for M2M relationships)
        if appointment.services.exists():
            appointment.total_price = appointment.calculate_total_price()
            appointment.save(update_fields=['total_price'])
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(appointment_date=today)
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments (next 7 days)"""
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        appointments = self.get_queryset().filter(
            appointment_date__range=[today, next_week],
            status__in=['scheduled', 'confirmed']
        )
        serializer = AppointmentListSerializer(appointments, many=True)
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
        """Get available time slots for a specific date and team member"""
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
        
        # Get existing appointments for the date and team member
        existing_appointments = Appointment.objects.filter(
            team_member_id=team_member_id,
            appointment_date=appointment_date,
            status__in=['scheduled', 'confirmed', 'in_progress']
        ).values_list('appointment_time', flat=True)
        
        # Generate available slots (9 AM to 6 PM, every 30 minutes)
        available_slots = []
        start_time = datetime.strptime('09:00', '%H:%M').time()
        end_time = datetime.strptime('18:00', '%H:%M').time()
        current_time = datetime.combine(appointment_date, start_time)
        end_datetime = datetime.combine(appointment_date, end_time)
        
        while current_time < end_datetime:
            if current_time.time() not in existing_appointments:
                available_slots.append(current_time.strftime('%H:%M'))
            current_time += timedelta(minutes=30)
        
        return Response({'available_slots': available_slots})
