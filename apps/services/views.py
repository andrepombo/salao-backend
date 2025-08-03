from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Service
from .serializers import ServiceSerializer, ServiceCreateUpdateSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new service and return full service data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        
        # Return full service data using ServiceSerializer
        response_serializer = ServiceSerializer(service)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a service and return full service data"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        
        # Return full service data using ServiceSerializer
        response_serializer = ServiceSerializer(service)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get services filtered by service type"""
        service_type = request.query_params.get('type')
        if service_type:
            services = Service.objects.filter(service_type=service_type, is_active=True)
            serializer = self.get_serializer(services, many=True)
            return Response(serializer.data)
        return Response([])
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get all available service types"""
        types = [{'value': choice[0], 'label': choice[1]} for choice in Service.SERVICE_TYPES]
        return Response(types)
