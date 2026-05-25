import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an admin superuser from ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv("ADMIN_USERNAME", "").strip()
        email = os.getenv("ADMIN_EMAIL", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")

        missing = [
            name
            for name, value in {
                "ADMIN_USERNAME": username,
                "ADMIN_EMAIL": email,
                "ADMIN_PASSWORD": password,
            }.items()
            if not value
        ]
        if missing:
            raise CommandError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING("Admin already exists"))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Admin created"))
