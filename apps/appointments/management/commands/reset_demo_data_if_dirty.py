from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.core.management import call_command


class Command(BaseCommand):
    help = "Reset salon demo data only if it has changed since the last reset."

    def handle(self, *args, **options):
        demo_mode = getattr(settings, "DEMO_MODE", False)
        if not demo_mode:
            self.stdout.write(self.style.WARNING("DEMO_MODE is disabled; skipping demo data reset."))
            return

        now_local = timezone.localtime(timezone.now())
        today = now_local.date().isoformat()

        last_key = "demo_salon_last_reset_date"
        dirty_key = "demo_salon_data_dirty"
        lock_key = "demo_salon_reset_lock"

        demo_dirty = cache.get(dirty_key, True)
        last_reset = cache.get(last_key)

        if not demo_dirty:
            if last_reset == today:
                self.stdout.write(
                    self.style.SUCCESS("Demo data already reset today and no new changes detected; skipping reseed.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("No demo data changes detected since last reset; skipping reseed.")
                )
            return

        if not cache.add(lock_key, "1", timeout=300):
            self.stdout.write(self.style.WARNING("Another demo reset appears to be running; aborting."))
            return

        try:
            self.stdout.write(self.style.WARNING("Changes detected in demo data; running salon demo reseed..."))
            call_command("seed_demo_salon", delete_existing=True)
            cache.set(last_key, today, timeout=172800)
            cache.set(dirty_key, False, timeout=172800)
            self.stdout.write(self.style.SUCCESS("Salon demo data reseeded successfully."))
        finally:
            cache.delete(lock_key)
