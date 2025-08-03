from django.db import models
from django.core.validators import RegexValidator


class Client(models.Model):
    """Model for salon clients"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    phone_regex = RegexValidator(
        regex=r'^\(\d{3}\) \d{5}-\d{4}$',
        message="Phone number must be entered in the format: '(xxx) xxxxx-xxxx'."
    )
    phone = models.CharField(validators=[phone_regex], max_length=16)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True, help_text="Client's date of birth")
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="Client's gender"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"

    class Meta:
        ordering = ['name']
