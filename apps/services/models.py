from django.db import models


class Service(models.Model):
    """Model for salon services"""
    SERVICE_TYPES = [
        ('cabelo', 'Cabelo'),
        ('unhas', 'Unhas'),
        ('barba', 'Barba'),
        ('maquiagem', 'Maquiagem'),
        ('pele', 'Pele'),
    ]
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        ordering = ['service_type', 'name']
