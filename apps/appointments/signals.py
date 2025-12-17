from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.clients.models import Client
from apps.services.models import Service
from apps.team.models import Team
from .models import Appointment


DEMO_SALON_DATA_DIRTY_FLAG = "demo_salon_data_dirty"


def _mark_demo_data_dirty():
    if not getattr(settings, "DEMO_MODE", False):
        return
    cache.set(DEMO_SALON_DATA_DIRTY_FLAG, True, timeout=172800)


@receiver(post_save, sender=Client)
def mark_demo_data_dirty_on_client_save(sender, instance, created, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_delete, sender=Client)
def mark_demo_data_dirty_on_client_delete(sender, instance, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_save, sender=Service)
def mark_demo_data_dirty_on_service_save(sender, instance, created, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_delete, sender=Service)
def mark_demo_data_dirty_on_service_delete(sender, instance, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_save, sender=Team)
def mark_demo_data_dirty_on_team_save(sender, instance, created, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_delete, sender=Team)
def mark_demo_data_dirty_on_team_delete(sender, instance, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_save, sender=Appointment)
def mark_demo_data_dirty_on_appointment_save(sender, instance, created, **kwargs):
    _mark_demo_data_dirty()


@receiver(post_delete, sender=Appointment)
def mark_demo_data_dirty_on_appointment_delete(sender, instance, **kwargs):
    _mark_demo_data_dirty()
