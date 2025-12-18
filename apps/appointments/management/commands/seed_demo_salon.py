import random
from datetime import date, timedelta, time, datetime

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

        svc_created, services = self._seed_services()
        cli_created, clients = self._seed_clients()
        team_created, team_members = self._seed_team(services)
        appt_created = self._seed_appointments(clients, team_members, services)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seeding summary:"))
        self.stdout.write(f"  Services created: {svc_created} (total now: {Service.objects.count()})")
        self.stdout.write(f"  Clients created: {cli_created} (total now: {Client.objects.count()})")
        self.stdout.write(f"  Team members created: {team_created} (total now: {Team.objects.count()})")
        self.stdout.write(f"  Appointments created: {appt_created} (total now: {Appointment.objects.count()})")
        self.stdout.write("")
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

        created_count = 0
        created = []
        for name, service_type, duration, price in base_services:
            obj, was_created = Service.objects.get_or_create(
                name=name,
                service_type=service_type,
                defaults={
                    "description": name,
                    "duration_minutes": duration,
                    "price": price,
                    "is_active": True,
                },
            )
            if was_created:
                created_count += 1
            created.append(obj)
        return created_count, created

    def _seed_clients(self):
        base_clients = [
            ("Ana Souza", "11987654321"),
            ("Bruno Lima", "11912345678"),
            ("Carla Ferreira", "11955556666"),
            ("Diego Santos", "11977778888"),
            ("Eduarda Almeida", "11999990000"),
        ]

        created_count = 0
        clients = []
        for name, phone in base_clients:
            obj, was_created = Client.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": f"{name.split()[0].lower()}@example.com",
                },
            )
            if was_created:
                created_count += 1
            clients.append(obj)
        return created_count, clients

    def _seed_team(self, services):
        base_team = [
            ("Marcos Oliveira", "11922223333"),
            ("Patrícia Costa", "11933334444"),
            ("Rafael Silva", "11944445555"),
        ]

        today = date.today()
        created_count = 0
        team_members = []
        for index, (name, phone) in enumerate(base_team):
            obj, was_created = Team.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "email": f"{name.split()[0].lower()}@example.com",
                    "hire_date": today - timedelta(days=365 * (index + 1)),
                    "is_active": True,
                },
            )
            if services:
                # Preserve existing specialties on reseed to avoid breaking existing appointments
                if was_created or obj.specialties.count() == 0:
                    specialties = random.sample(services, k=min(3, len(services)))
                    obj.specialties.set(specialties)
            if was_created:
                created_count += 1
            team_members.append(obj)
        return created_count, team_members

    def _seed_appointments(self, clients, team_members, services):
        if not clients or not team_members or not services:
            return 0

        base_date = date.today()
        base_time = time(hour=10, minute=0)

        statuses = [
            "scheduled",
            "confirmed",
            "in_progress",
            "completed",
            "cancelled",
            "no_show",
        ]

        # Build pools: ensure at least 5 on today; prefer future times today, fallback to past times if needed
        today = date.today()
        now_time = datetime.now().time()
        today_future_slots = []
        today_past_slots = []
        other_slots = []
        for team_member in team_members:
            for day_offset in range(0, 6):
                for hour_offset in [0, 1, 2, 3]:
                    appt_date = base_date + timedelta(days=day_offset)
                    appt_time = time(hour=base_time.hour + hour_offset, minute=0)
                    if appt_date == today:
                        if appt_time > now_time:
                            today_future_slots.append((team_member, appt_date, appt_time))
                        else:
                            today_past_slots.append((team_member, appt_date, appt_time))
                    else:
                        other_slots.append((team_member, appt_date, appt_time))

        random.shuffle(today_future_slots)
        random.shuffle(today_past_slots)
        random.shuffle(other_slots)

        # Assemble candidate list ensuring at least 5 from today
        NEED_TODAY = 5
        TOTAL_NEEDED = 15

        def try_create(team_member, appt_date, appt_time):
            if Appointment.objects.filter(
                team_member=team_member,
                appointment_date=appt_date,
                appointment_time=appt_time,
            ).exists():
                return False
            client = random.choice(clients)
            status = random.choice(statuses)
            appointment = Appointment.objects.create(
                client=client,
                team_member=team_member,
                appointment_date=appt_date,
                appointment_time=appt_time,
                status=status,
            )
            specialties_qs = team_member.specialties.all()
            specialties = list(specialties_qs)
            source_pool = specialties if len(specialties) > 0 else services
            k_max = min(3, len(source_pool))
            k = random.randint(1, k_max) if k_max > 0 else 0
            chosen_services = random.sample(source_pool, k=k) if k > 0 else []
            appointment.services.set(chosen_services)
            appointment.total_price = appointment.calculate_total_price()
            appointment.save(update_fields=["total_price"])
            return True

        # Create up to 15 appointments in free slots, prioritizing at least 5 today
        created_count = 0
        todays_created = 0
        for team_member, appt_date, appt_time in today_future_slots + today_past_slots:
            if try_create(team_member, appt_date, appt_time):
                created_count += 1
                todays_created += 1
                if todays_created >= NEED_TODAY or created_count >= TOTAL_NEEDED:
                    break
        if created_count < TOTAL_NEEDED:
            for team_member, appt_date, appt_time in today_future_slots + today_past_slots + other_slots:
                if created_count >= TOTAL_NEEDED:
                    break
                if try_create(team_member, appt_date, appt_time):
                    created_count += 1

        return created_count
