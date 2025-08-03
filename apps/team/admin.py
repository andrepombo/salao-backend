from django.contrib import admin
from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'hire_date', 'is_active']
    list_filter = ['is_active', 'hire_date', 'specialties']
    search_fields = ['name', 'phone', 'email']
    filter_horizontal = ['specialties']
    ordering = ['name']
