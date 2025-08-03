from django.db import models
from django.core.validators import RegexValidator
from apps.services.models import Service


class Team(models.Model):
    """Model for salon team members (hairdressers)"""
    name = models.CharField(max_length=100)
    phone_regex = RegexValidator(
        regex=r'^\d{11}$',
        message="Phone number must contain exactly 11 digits."
    )
    phone = models.CharField(validators=[phone_regex], max_length=11)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    specialties = models.ManyToManyField(
        Service,
        related_name='specialists',
        help_text="Services this team member can provide"
    )
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def formatted_phone(self):
        """Format phone number as (xx) xxxxx-xxxx"""
        if len(self.phone) == 11:
            return f"({self.phone[:2]}) {self.phone[2:7]}-{self.phone[7:]}"
        return self.phone
    
    def __str__(self):
        return f"{self.name} - {self.formatted_phone()}"

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Team Members"
