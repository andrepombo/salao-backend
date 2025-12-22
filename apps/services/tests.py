import pytest

# Create your tests here.

@pytest.mark.django_db
def test_create_simple_service(service_factory):
    service = service_factory(
        name="Corte básico",
        service_type="cabelo",
        description="Corte simples de cabelo",
        duration_minutes=30,
        price="50.00",
    )

    assert service.name == "Corte básico"
    assert service.service_type == "cabelo"
    assert service.is_active is True
    assert "Corte básico" in str(service)


@pytest.mark.django_db
@pytest.mark.parametrize("service_type", ["cabelo", "unhas", "barba"]) 
def test_create_service_with_various_types(service_factory, service_type):
    service = service_factory(
        name=f"Serviço {service_type}",
        service_type=service_type,
        duration_minutes=15,
        price="10.00",
    )

    assert service.service_type == service_type
    assert service.pk is not None
