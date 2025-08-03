from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Service
from .serializers import ServiceSerializer, ServiceCreateSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceCreateSerializer
        return ServiceSerializer
    
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
