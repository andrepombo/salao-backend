from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import models
from .models import Client
from .serializers import ClientSerializer, ClientCreateSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
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
