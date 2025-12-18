from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
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


@receiver(pre_save, sender=Team)
def _cache_previous_active_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous = Team.objects.get(pk=instance.pk)
            instance._was_active = previous.is_active
        except Team.DoesNotExist:
            instance._was_active = instance.is_active
    else:
        instance._was_active = instance.is_active


@receiver(post_save, sender=Team)
def delete_appointments_when_team_inactivated(sender, instance, created, **kwargs):
    if created:
        return
    was_active = getattr(instance, "_was_active", None)
    if was_active is True and instance.is_active is False:
        Appointment.objects.filter(team_member=instance).exclude(status__in=["completed", "cancelled"]).delete()

@receiver(pre_delete, sender=Team)
def delete_nonfinal_appointments_on_team_delete(sender, instance, **kwargs):
    Appointment.objects.filter(team_member=instance).exclude(status__in=["completed", "cancelled"]).delete()

