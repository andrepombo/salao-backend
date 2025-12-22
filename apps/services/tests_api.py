import pytest

from .models import Service


@pytest.mark.django_db
def test_list_services_returns_active_only(api_client, service_factory):
    service_factory(name="Ativo 1", service_type="cabelo", duration_minutes=30, price="50.00", is_active=True)
    service_factory(name="Inativo", service_type="unhas", duration_minutes=20, price="30.00", is_active=False)
    service_factory(name="Ativo 2", service_type="barba", duration_minutes=15, price="25.00", is_active=True)

    resp = api_client.get("/api/services/")

    assert resp.status_code == 200
    data = resp.json()
    names = {item["name"] for item in data}
    assert names == {"Ativo 1", "Ativo 2"}


@pytest.mark.django_db
def test_services_types_endpoint_lists_choices(api_client):
    resp = api_client.get("/api/services/types/")

    assert resp.status_code == 200
    data = resp.json()
    # Ensure at least known entries are present
    values = {item["value"] for item in data}
    assert {"cabelo", "unhas", "barba"}.issubset(values)


@pytest.mark.django_db
def test_services_by_type_filters_correctly(api_client, service_factory):
    service_factory(name="Corte", service_type="cabelo", duration_minutes=30, price="50.00")
    service_factory(name="Manicure", service_type="unhas", duration_minutes=40, price="60.00")

    resp = api_client.get("/api/services/by_type/", {"type": "cabelo"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["service_type"] == "cabelo"


@pytest.mark.django_db
def test_create_service_returns_full_data(api_client):
    payload = {
        "name": "Corte premium",
        "service_type": "cabelo",
        "description": "Corte especial",
        "duration_minutes": 45,
        "price": "120.00",
        "is_active": True,
    }

    resp = api_client.post("/api/services/", data=payload, format="json")

    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["name"] == payload["name"]
    assert data["service_type"] == payload["service_type"]
    assert data["duration_minutes"] == payload["duration_minutes"]
    assert data["price"] == payload["price"]


@pytest.mark.django_db
def test_update_service_returns_updated_data(api_client, service_factory):
    service = service_factory(name="Corte simples", price="50.00")

    resp = api_client.patch(
        f"/api/services/{service.id}/",
        data={"name": "Corte atualizado", "price": "80.00"},
        format="json",
    )

    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert data["name"] == "Corte atualizado"
    assert data["price"] == "80.00"
