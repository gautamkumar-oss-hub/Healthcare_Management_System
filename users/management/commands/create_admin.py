
import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create or update the initial Django administrator"

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")
        email = os.environ.get("ADMIN_EMAIL", "")

        if not username or not password:
            raise CommandError(
                "ADMIN_USERNAME and ADMIN_PASSWORD are required."
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True

        if hasattr(user, "user_type"):
            user.user_type = "staff"

        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Administrator {'created' if created else 'updated'} successfully."
            )
        )
