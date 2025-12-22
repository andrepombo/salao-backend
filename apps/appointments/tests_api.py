import datetime as dt
import pytest

from apps.services.models import Service
from apps.appointments.models import Appointment


@pytest.mark.django_db
def test_create_appointment_success_no_overlap(api_client, client_factory, team_factory, service_factory):
    # Arrange: client, team, services and specialties
    client = client_factory()
    team = team_factory()
    s1 = service_factory(name="Corte", service_type="cabelo", duration_minutes=30)
    s2 = service_factory(name="Barba", service_type="barba", duration_minutes=30)
    team.specialties.set([s1, s2])

    date = dt.date.today() + dt.timedelta(days=1)

    # Act: create first appointment at 10:00 (60 minutes total)
    resp = api_client.post(
        "/api/appointments/",
        data={
            "client": client.id,
            "team_member": team.id,
            "services": [s1.id, s2.id],
            "appointment_date": date.isoformat(),
            "appointment_time": "10:00",
            "status": "scheduled",
        },
        format="json",
    )

    # Assert first creation
    assert resp.status_code == 201, resp.content
    created = resp.json()
    assert created["client"] == client.id
    assert created["team_member"]["id"] == team.id

    # Sanity: ensure total duration method works (via model helper)
    appt = Appointment.objects.get(id=created["id"])  # type: ignore[index]
    assert appt.calculate_total_duration() == 60


@pytest.mark.django_db
def test_create_appointment_overlap_rejected(api_client, client_factory, team_factory, service_factory):
    # Arrange base entities
    client = client_factory()
    team = team_factory()
    s1 = service_factory(name="Corte", service_type="cabelo", duration_minutes=45)
    team.specialties.set([s1])

    date = dt.date.today() + dt.timedelta(days=1)

    # Create existing appointment from 10:00 to 10:45
    resp1 = api_client.post(
        "/api/appointments/",
        data={
            "client": client.id,
            "team_member": team.id,
            "services": [s1.id],
            "appointment_date": date.isoformat(),
            "appointment_time": "10:00",
            "status": "scheduled",
        },
        format="json",
    )
    assert resp1.status_code == 201, resp1.content

    # Attempt overlapping appointment starting at 10:30 (overlaps existing 10:00-10:45)
    resp2 = api_client.post(
        "/api/appointments/",
        data={
            "client": client.id,
            "team_member": team.id,
            "services": [s1.id],
            "appointment_date": date.isoformat(),
            "appointment_time": "10:30",
            "status": "scheduled",
        },
        format="json",
    )

    assert resp2.status_code == 400
    # Error message is raised by serializer; just assert there is a validation error
    assert "Conflito" in resp2.content.decode() or "conflit" in resp2.content.decode().lower()
