import random
from datetime import date, timedelta, time

from django.core.management.base import BaseCommand

from apps.clients.models import Client
from apps.services.models import Service
from apps.team.models import Team
from apps.appointments.models import Appointment


class Command(BaseCommand):
    help = "Seed demo data for salon clients, services, team, and appointments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-existing",
            action="store_true",
            help="Delete existing salon data before seeding",
        )

    def handle(self, *args, **options):
        delete_existing = options.get("delete_existing", False)

        if delete_existing:
            self.stdout.write(self.style.WARNING("Deleting existing salon data (appointments, team, clients, services)..."))
            Appointment.objects.all().delete()
            Team.objects.all().delete()
            Client.objects.all().delete()
            Service.objects.all().delete()

        services = self._seed_services()
        clients = self._seed_clients()
        team_members = self._seed_team(services)
        self._seed_appointments(clients, team_members, services)

        self.stdout.write(self.style.SUCCESS("Demo salon data seeded successfully."))

    def _seed_services(self):
        base_services = [
            ("Corte feminino", "cabelo", 60, 120.00),
            ("Corte masculino", "cabelo", 45, 80.00),
            ("Coloração completa", "cabelo", 120, 300.00),
            ("Manicure", "unhas", 40, 60.00),
            ("Pedicure", "unhas", 50, 70.00),
            ("Barba completa", "barba", 30, 50.00),
            ("Maquiagem social", "maquiagem", 75, 180.00),
            ("Limpeza de pele", "pele", 60, 150.00),
        ]

        created = []
        for name, service_type, duration, price in base_services:
            obj, _ = Service.objects.get_or_create(
                name=name,
                service_type=service_type,
                defaults={
                    "description": name,
                    "duration_minutes": duration,
                    "price": price,
                    "is_active": True,
                },
            )
            created.append(obj)
        return created

    def _seed_clients(self):
        base_clients = [
            ("Ana Souza", "11987654321"),
            ("Bruno Lima", "11912345678"),
            ("Carla Ferreira", "11955556666"),
            ("Diego Santos", "11977778888"),
            ("Eduarda Almeida", "11999990000"),
        ]

        clients = []
        for name, phone in base_clients:
            obj, _ = Client.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": f"{name.split()[0].lower()}@example.com",
                },
            )
            clients.append(obj)
        return clients

    def _seed_team(self, services):
        base_team = [
            ("Marcos Oliveira", "11922223333"),
            ("Patrícia Costa", "11933334444"),
            ("Rafael Silva", "11944445555"),
        ]

        today = date.today()
        team_members = []
        for index, (name, phone) in enumerate(base_team):
            obj, _ = Team.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": f"{name.split()[0].lower()}@example.com",
                    "hire_date": today - timedelta(days=365 * (index + 1)),
                    "is_active": True,
                },
            )
            if services:
                specialties = random.sample(services, k=min(3, len(services)))
                obj.specialties.set(specialties)
            team_members.append(obj)
        return team_members

    def _seed_appointments(self, clients, team_members, services):
        if not clients or not team_members or not services:
            return

        base_date = date.today() + timedelta(days=1)
        base_time = time(hour=10, minute=0)

        statuses = [
            "scheduled",
            "confirmed",
            "in_progress",
            "completed",
            "cancelled",
            "no_show",
        ]

        # Build a pool of possible unique slots per team member and time window
        slots = []
        for team_member in team_members:
            for day_offset in range(0, 6):
                for hour_offset in [0, 1, 2, 3]:
                    appt_date = base_date + timedelta(days=day_offset)
                    appt_time = time(hour=base_time.hour + hour_offset, minute=0)
                    slots.append((team_member, appt_date, appt_time))

        random.shuffle(slots)

        # Create up to 10 appointments in free slots
        for team_member, appt_date, appt_time in slots[:10]:
            # Skip if something already exists for this slot (safety when not deleting existing data)
            if Appointment.objects.filter(
                team_member=team_member,
                appointment_date=appt_date,
                appointment_time=appt_time,
            ).exists():
                continue

            client = random.choice(clients)
            status = random.choice(statuses)

            appointment = Appointment.objects.create(
                client=client,
                team_member=team_member,
                appointment_date=appt_date,
                appointment_time=appt_time,
                status=status,
            )

            chosen_services = random.sample(services, k=random.randint(1, min(3, len(services))))
            appointment.services.set(chosen_services)
            appointment.total_price = appointment.calculate_total_price()
            appointment.save(update_fields=["total_price"])
