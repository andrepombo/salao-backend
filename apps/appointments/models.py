from django.db import models
from apps.clients.models import Client
from apps.services.models import Service
from apps.team.models import Team


class Appointment(models.Model):
    """Model for salon appointments"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    team_member = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    services = models.ManyToManyField(
        Service,
        related_name='appointments',
        help_text="Services to be provided in this appointment"
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    notes = models.TextField(blank=True, null=True)
    total_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total_price(self):
        """Calculate total price from all services"""
        return sum(service.price for service in self.services.all())
    
    def calculate_total_duration(self):
        """Calculate total duration from all services in minutes"""
        return sum(service.duration_minutes for service in self.services.all())
    
    def get_services_list(self):
        """Get comma-separated list of service names"""
        return ", ".join(service.name for service in self.services.all())

    def save(self, *args, **kwargs):
        # Save first, then calculate total price from services
        super().save(*args, **kwargs)
        if not self.total_price and self.services.exists():
            self.total_price = self.calculate_total_price()
            super().save(update_fields=['total_price'])

    def __str__(self):
        services_str = self.get_services_list() or "No services"
        return f"{self.client.name} - {self.team_member.name} - {services_str} - {self.appointment_date} {self.appointment_time}"

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['team_member', 'appointment_date', 'appointment_time']
