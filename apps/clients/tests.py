from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from datetime import date, timedelta, time
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from apps.appointments.models import Appointment
from apps.team.models import Team
from apps.services.models import Service


class ClientModelTests(TestCase):
    def test_phone_validation_accepts_11_digits(self):
        client = Client.objects.create(
            name="Maria Silva",
            phone="11987654321",
            email="maria@example.com",
        )
        self.assertEqual(client.phone, "11987654321")

    def test_phone_validation_rejects_non_11_digits(self):
        c1 = Client(name="João", phone="1234567890")  # 10 digits
        with self.assertRaises(ValidationError):
            c1.full_clean()
        c2 = Client(name="Carla", phone="abc")  # non-digits
        with self.assertRaises(ValidationError):
            c2.full_clean()

    def test_formatted_phone(self):
        c = Client.objects.create(name="Ana", phone="11912345678")
        self.assertEqual(c.formatted_phone(), "(11) 91234-5678")


class ClientSerializerTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Pedro",
            phone="11900000000",
            email="pedro@example.com",
        )
        self.team = Team.objects.create(name="Profissional A", phone="11911111111", hire_date=date.today())
        self.service = Service.objects.create(name="Corte", price=50.00, duration_minutes=30)

        # Two appointments on different dates
        a1 = Appointment.objects.create(
            client=self.client_obj,
            team_member=self.team,
            appointment_date=date(2025, 1, 10),
            appointment_time=time(10, 0),
            status="completed",
        )
        a1.services.add(self.service)

        a2 = Appointment.objects.create(
            client=self.client_obj,
            team_member=self.team,
            appointment_date=date(2025, 2, 5),
            appointment_time=time(11, 0),
            status="confirmed",
        )
        a2.services.add(self.service)

    def test_serializer_includes_computed_fields(self):
        data = ClientSerializer(self.client_obj).data
        self.assertIn("formatted_phone", data)
        self.assertIn("appointments_count", data)
        self.assertIn("last_appointment", data)
        self.assertEqual(data["appointments_count"], 2)
        self.assertEqual(str(data["last_appointment"]), "2025-02-05")


class ClientAPITests(APITestCase):
    def setUp(self):
        # Common objects
        self.team = Team.objects.create(name="Profissional B", phone="11922222222", hire_date=date.today())
        self.service = Service.objects.create(name="Manicure", price=40.00, duration_minutes=45)

        # Seed different clients for filtering
        self.c1 = Client.objects.create(name="Alice", phone="11911111111", email="alice@example.com", gender="F")
        self.c2 = Client.objects.create(name="Bruno", phone="11922222222", email="bruno@example.com", gender="M")
        self.c3 = Client.objects.create(name="Carlos", phone="11933333333", email="carlos@sample.com", gender="M")

        # Adjust created_at to test date range filters
        Client.objects.filter(pk=self.c1.pk).update(created_at=timezone.now() - timedelta(days=40))
        Client.objects.filter(pk=self.c2.pk).update(created_at=timezone.now() - timedelta(days=10))
        Client.objects.filter(pk=self.c3.pk).update(created_at=timezone.now() - timedelta(days=3))

    def test_create_client_returns_full_representation(self):
        url = reverse("client-list")
        payload = {
            "name": "Daniela",
            "phone": "11944444444",
            "email": "dani@example.com",
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", resp.data)
        self.assertIn("formatted_phone", resp.data)
        self.assertEqual(resp.data["formatted_phone"], "(11) 94444-4444")

    def test_create_client_invalid_phone(self):
        url = reverse("client-list")
        resp = self.client.post(url, {"name": "Eli", "phone": "123"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_client_returns_full_representation(self):
        url = reverse("client-detail", args=[self.c1.id])
        resp = self.client.put(url, {"name": "Alice Nova", "phone": "11911111111"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Alice Nova")
        self.assertIn("formatted_phone", resp.data)

    def test_list_clients_filters(self):
        url = reverse("client-list")
        # Filter by partial name (icontains)
        r1 = self.client.get(url, {"name": "li"})
        self.assertTrue(any(c["name"] == "Alice" for c in r1.data))

        # Filter by phone (partial)
        r2 = self.client.get(url, {"phone": "2222"})
        self.assertTrue(any(c["name"] == "Bruno" for c in r2.data))

        # Filter by email (icontains)
        r3 = self.client.get(url, {"email": "sample.com"})
        self.assertTrue(any(c["name"] == "Carlos" for c in r3.data))

        # Filter by gender
        r4 = self.client.get(url, {"gender": "M"})
        self.assertTrue(all(c["gender"] == "M" for c in r4.data))

        # Date range filters (created_at)
        start = (timezone.now() - timedelta(days=15)).date().isoformat()
        end = timezone.now().date().isoformat()
        r5 = self.client.get(url, {"start_date": start, "end_date": end})
        # Only c2 (10 days) and c3 (3 days) should be included
        names = [c["name"] for c in r5.data]
        self.assertIn("Bruno", names)
        self.assertIn("Carlos", names)
        self.assertNotIn("Alice", names)

    def test_search_action(self):
        url = reverse("client-search")
        r = self.client.get(url, {"q": "bru"})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(any(c["name"] == "Bruno" for c in r.data))

    def test_recent_action(self):
        url = reverse("client-recent")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        # c2 (10 days) and c3 (3 days) are within last 30 days
        names = [c["name"] for c in r.data]
        self.assertIn("Bruno", names)
        self.assertIn("Carlos", names)
        self.assertNotIn("Alice", names)  # 40 days ago

    def test_stats_action(self):
        # Add one appointment for c2 to ensure serializer-related fields don't break
        apt = Appointment.objects.create(
            client=self.c2,
            team_member=self.team,
            appointment_date=date.today(),
            appointment_time=time(9, 0),
            status="confirmed",
        )
        apt.services.add(self.service)

        url = reverse("client-stats")
        r = self.client.get(url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("total_clients", r.data)
        self.assertIn("gender_distribution", r.data)
        self.assertIn("monthly_registrations", r.data)
        self.assertGreaterEqual(r.data["total_clients"], 3)


# Create your tests here.
