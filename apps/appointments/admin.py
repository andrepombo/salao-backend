from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'team_member', 'get_services_display', 'appointment_date', 'appointment_time', 'status', 'total_price', 'get_total_duration']
    list_filter = ['status', 'appointment_date', 'services__service_type', 'team_member']
    search_fields = ['client__name', 'team_member__name', 'services__name']
    filter_horizontal = ['services']
    date_hierarchy = 'appointment_date'
    ordering = ['appointment_date', 'appointment_time']
    
    def get_services_display(self, obj):
        return obj.get_services_list()
    get_services_display.short_description = 'Services'
    
    def get_total_duration(self, obj):
        duration = obj.calculate_total_duration()
        return f"{duration} min" if duration else "0 min"
    get_total_duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'team_member').prefetch_related('services')
