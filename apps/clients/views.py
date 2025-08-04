from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Client
from .serializers import ClientSerializer, ClientCreateUpdateSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()  # Required for Django REST framework router
    serializer_class = ClientSerializer
    
    def get_queryset(self):
        """Optimized queryset with efficient filtering and prefetching"""
        # Prefetch appointments for better performance when serializing
        queryset = Client.objects.prefetch_related('appointments')
        
        # Build filters efficiently
        filters = Q()
        
        # Filter by name
        name = self.request.query_params.get('name')
        if name:
            filters &= Q(name__icontains=name)
            
        # Filter by phone
        phone = self.request.query_params.get('phone')
        if phone:
            filters &= Q(phone__icontains=phone)
            
        # Filter by email
        email = self.request.query_params.get('email')
        if email:
            filters &= Q(email__icontains=email)
            
        # Filter by gender
        gender = self.request.query_params.get('gender')
        if gender:
            filters &= Q(gender=gender)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            filters &= Q(created_at__gte=start_date)
        if end_date:
            filters &= Q(created_at__lte=end_date)
        
        # Apply all filters at once
        if filters:
            queryset = queryset.filter(filters)
            
        return queryset.order_by('name')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ClientCreateUpdateSerializer
        return ClientSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new client and return full client data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        
        # Return full client data using ClientSerializer
        response_serializer = ClientSerializer(client)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a client and return full client data"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        client = serializer.save()
        
        # Return full client data using ClientSerializer
        response_serializer = ClientSerializer(client)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search clients by name or phone - optimized with caching"""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
            
        # Cache key for search results
        cache_key = f'clients_search_{query.lower()}'
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            return Response(cached_results)
        
        # Optimized search query with prefetching
        clients = Client.objects.filter(
            Q(name__icontains=query) | 
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        ).prefetch_related('appointments').order_by('name')
        
        serializer = self.get_serializer(clients, many=True)
        
        # Cache for 10 minutes
        cache.set(cache_key, serializer.data, 600)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently created clients - optimized with caching"""
        cache_key = 'clients_recent'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Get clients created in the last 30 days with prefetching
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_clients = Client.objects.filter(
            created_at__gte=thirty_days_ago
        ).prefetch_related('appointments').order_by('-created_at')[:20]
        
        serializer = self.get_serializer(recent_clients, many=True)
        
        # Cache for 5 minutes
        cache.set(cache_key, serializer.data, 300)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get client statistics - optimized with caching"""
        cache_key = 'clients_stats'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Calculate statistics efficiently
        from django.db.models import Count
        
        total_clients = Client.objects.count()
        
        # Gender distribution
        gender_stats = Client.objects.values('gender').annotate(
            count=Count('gender')
        ).order_by('gender')
        
        # Clients by month (last 12 months)
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_stats = Client.objects.filter(
            created_at__gte=twelve_months_ago
        ).extra(
            select={'month': "strftime('%%Y-%%m', created_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        stats_data = {
            'total_clients': total_clients,
            'gender_distribution': list(gender_stats),
            'monthly_registrations': list(monthly_stats)
        }
        
        # Cache for 15 minutes
        cache.set(cache_key, stats_data, 900)
        return Response(stats_data)
