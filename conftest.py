import datetime as dt
import pytest
from rest_framework.test import APIClient

from apps.services.models import Service
from apps.clients.models import Client
from apps.team.models import Team


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def service_factory(db):
    def make_service(**kwargs):
        defaults = dict(
            name="Servico",
            service_type="cabelo",
            duration_minutes=30,
            price="50.00",
            is_active=True,
        )
        defaults.update(kwargs)
        return Service.objects.create(**defaults)
    return make_service


@pytest.fixture
def client_factory(db):
    def make_client(**kwargs):
        defaults = dict(
            name="Joao",
            phone="11999999999",
        )
        defaults.update(kwargs)
        return Client.objects.create(**defaults)
    return make_client


@pytest.fixture
def team_factory(db):
    def make_team(**kwargs):
        defaults = dict(
            name="Profissional",
            phone="11988888888",
            hire_date=dt.date.today(),
            is_active=True,
        )
        defaults.update(kwargs)
        return Team.objects.create(**defaults)
    return make_team
