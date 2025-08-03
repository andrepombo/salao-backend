from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Team
from .serializers import TeamSerializer, TeamCreateSerializer, TeamListSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_active=True)
    serializer_class = TeamSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TeamCreateSerializer
        elif self.action == 'list':
            return TeamListSerializer
        return TeamSerializer
    
    def get_queryset(self):
        queryset = Team.objects.filter(is_active=True)
        return queryset.prefetch_related('specialties')
    
    @action(detail=False, methods=['get'])
    def available_for_service(self, request):
        """Get team members who can provide a specific service"""
        service_id = request.query_params.get('service_id')
        if service_id:
            team_members = Team.objects.filter(
                specialties__id=service_id,
                is_active=True
            ).distinct()
            serializer = TeamListSerializer(team_members, many=True)
            return Response(serializer.data)
        return Response([])
