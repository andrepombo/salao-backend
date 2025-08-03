from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'duration_minutes', 'price', 'is_active']
    list_filter = ['service_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['service_type', 'name']
