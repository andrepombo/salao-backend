import pytest
from rest_framework.test import APIClient

from .models import Service


@pytest.mark.django_db
def test_list_services_returns_active_only():
    Service.objects.create(name="Ativo 1", service_type="cabelo", duration_minutes=30, price="50.00", is_active=True)
    Service.objects.create(name="Inativo", service_type="unhas", duration_minutes=20, price="30.00", is_active=False)
    Service.objects.create(name="Ativo 2", service_type="barba", duration_minutes=15, price="25.00", is_active=True)

    client = APIClient()
    resp = client.get("/api/services/")

    assert resp.status_code == 200
    data = resp.json()
    names = {item["name"] for item in data}
    assert names == {"Ativo 1", "Ativo 2"}


@pytest.mark.django_db
def test_services_types_endpoint_lists_choices():
    client = APIClient()
    resp = client.get("/api/services/types/")

    assert resp.status_code == 200
    data = resp.json()
    # Ensure at least known entries are present
    values = {item["value"] for item in data}
    assert {"cabelo", "unhas", "barba"}.issubset(values)


@pytest.mark.django_db
def test_services_by_type_filters_correctly():
    Service.objects.create(name="Corte", service_type="cabelo", duration_minutes=30, price="50.00")
    Service.objects.create(name="Manicure", service_type="unhas", duration_minutes=40, price="60.00")

    client = APIClient()
    resp = client.get("/api/services/by_type/", {"type": "cabelo"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["service_type"] == "cabelo"
