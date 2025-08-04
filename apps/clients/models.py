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
        regex=r'^\d{11}$',
        message="Phone number must contain exactly 11 digits."
    )
    phone = models.CharField(validators=[phone_regex], max_length=11)
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

    def formatted_phone(self):
        """Format phone number as (xx) xxxxx-xxxx"""
        if len(self.phone) == 11:
            return f"({self.phone[:2]}) {self.phone[2:7]}-{self.phone[7:]}"
        return self.phone
    
    def __str__(self):
        return f"{self.name} - {self.formatted_phone()}"

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['birthday']),
            models.Index(fields=['gender']),
        ]
