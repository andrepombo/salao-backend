import datetime as dt
import pytest
from django.utils import timezone

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


@pytest.mark.django_db
def test_appointments_today_endpoint_returns_today_appointments(
    api_client, client_factory, team_factory, service_factory
):
    today = timezone.now().date()
    other_day = today + dt.timedelta(days=3)

    client = client_factory()
    team = team_factory()
    service = service_factory(duration_minutes=30)
    team.specialties.set([service])

    # Today appointment
    appt_today = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=today,
        appointment_time=dt.time(10, 0),
        status="scheduled",
    )
    appt_today.services.set([service])

    # Another day appointment
    appt_other = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=other_day,
        appointment_time=dt.time(11, 0),
        status="scheduled",
    )
    appt_other.services.set([service])

    resp = api_client.get("/api/appointments/today/")
    assert resp.status_code == 200
    data = resp.json()
    dates = {item["appointment_date"] for item in data}
    assert str(today) in dates
    assert str(other_day) not in dates


@pytest.mark.django_db
def test_appointments_upcoming_endpoint_returns_next_7_days(
    api_client, client_factory, team_factory, service_factory
):
    today = timezone.now().date()
    within_range = today + dt.timedelta(days=3)
    outside_range = today + dt.timedelta(days=10)

    client = client_factory()
    team = team_factory()
    service = service_factory(duration_minutes=30)
    team.specialties.set([service])

    appt_within = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=within_range,
        appointment_time=dt.time(9, 0),
        status="scheduled",
    )
    appt_within.services.set([service])

    appt_outside = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=outside_range,
        appointment_time=dt.time(9, 0),
        status="scheduled",
    )
    appt_outside.services.set([service])

    resp = api_client.get("/api/appointments/upcoming/")
    assert resp.status_code == 200
    data = resp.json()
    dates = {item["appointment_date"] for item in data}
    assert str(within_range) in dates
    assert str(outside_range) not in dates


@pytest.mark.django_db
def test_appointments_stats_endpoint_aggregates_data(
    api_client, client_factory, team_factory, service_factory
):
    today = timezone.now().date()

    client = client_factory()
    team = team_factory()
    service = service_factory(duration_minutes=30)
    team.specialties.set([service])

    # One completed appointment today with known total_price
    appt_today = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=today,
        appointment_time=dt.time(10, 0),
        status="completed",
        total_price=100,
    )
    appt_today.services.set([service])

    resp = api_client.get("/api/appointments/stats/")
    assert resp.status_code == 200
    data = resp.json()

    assert data["today_appointments_count"] >= 1
    assert data["today_revenue"] >= 100.0
    assert data["month_revenue"] >= data["today_revenue"]


@pytest.mark.django_db
def test_available_slots_excludes_occupied_times(
    api_client, client_factory, team_factory, service_factory
):
    date = (timezone.now().date() + dt.timedelta(days=1))

    client = client_factory()
    team = team_factory()
    service = service_factory(duration_minutes=60)
    team.specialties.set([service])

    # Appointment from 10:00 to 11:00 blocks 10:00 and 10:30 slots
    appt = Appointment.objects.create(
        client=client,
        team_member=team,
        appointment_date=date,
        appointment_time=dt.time(10, 0),
        status="scheduled",
    )
    appt.services.set([service])

    resp = api_client.get(
        "/api/appointments/available_slots/",
        {"date": date.isoformat(), "team_member": team.id},
    )
    assert resp.status_code == 200
    data = resp.json()
    slots = data.get("available_slots", [])

    assert "10:00" not in slots
    assert "10:30" not in slots
    # Neighboring slots should still be available
    assert "09:00" in slots
    assert "11:00" in slots
