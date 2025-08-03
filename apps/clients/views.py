from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from .models import Client
from .serializers import ClientSerializer, ClientCreateUpdateSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    
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
        """Search clients by name or phone"""
        query = request.query_params.get('q', '')
        if query:
            clients = Client.objects.filter(
                models.Q(name__icontains=query) | 
                models.Q(phone__icontains=query)
            )
            serializer = self.get_serializer(clients, many=True)
            return Response(serializer.data)
        return Response([])
