import datetime as dt

import pytest

from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentCreateSerializer, AppointmentListSerializer


@pytest.mark.django_db
def test_appointment_create_serializer_rejects_services_not_in_team_specialties(
    client_factory, team_factory, service_factory
):
    client = client_factory()
    team = team_factory()
    s1 = service_factory(name="Corte", service_type="cabelo", duration_minutes=30)
    s2 = service_factory(name="Manicure", service_type="unhas", duration_minutes=30)
    team.specialties.set([s1])  # profissional só oferece s1

    date = dt.date.today() + dt.timedelta(days=1)

    serializer = AppointmentCreateSerializer(
        data={
            "client": client.id,
            "team_member": team.id,
            "services": [s1.id, s2.id],
            "appointment_date": date.isoformat(),
            "appointment_time": "10:00",
            "status": "scheduled",
            "notes": "",
        }
    )

    assert not serializer.is_valid()
    # Mensagem de erro geral (non_field_errors)
    assert "O profissional selecionado" in str(serializer.errors)


@pytest.mark.django_db
def test_appointment_list_serializer_uses_prefetched_services_and_duration(
    client_factory, team_factory, service_factory
):
    client = client_factory()
    team = team_factory()
    s1 = service_factory(name="Corte", duration_minutes=30)
    s2 = service_factory(name="Barba", duration_minutes=45)
    team.specialties.set([s1, s2])

    date = dt.date.today() + dt.timedelta(days=1)
    appointment = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=date,
        appointment_time=dt.time(10, 0),
        status="scheduled",
    )
    appointment.services.set([s1, s2])

    # Prefetch to populate _prefetched_objects_cache
    qs = Appointment.objects.prefetch_related("services").filter(id=appointment.id)
    appointment_prefetched = qs[0]

    serializer = AppointmentListSerializer(appointment_prefetched)
    data = serializer.data

    assert data["services_list"]
    assert "Corte" in data["services_list"]
    assert "Barba" in data["services_list"]
    assert data["total_duration"] == s1.duration_minutes + s2.duration_minutes
