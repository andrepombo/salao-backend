from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import Team
from .serializers import TeamSerializer, TeamCreateUpdateSerializer, TeamListSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.filter(is_active=True)
    serializer_class = TeamSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TeamCreateUpdateSerializer
        elif self.action == 'list':
            return TeamListSerializer
        return TeamSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new team member and return full team data"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team_member = serializer.save()
        
        # Return full team data using TeamSerializer
        response_serializer = TeamSerializer(team_member)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update a team member and return full team data"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        team_member = serializer.save()
        
        # Return full team data using TeamSerializer
        response_serializer = TeamSerializer(team_member)
        return Response(response_serializer.data)
    
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
