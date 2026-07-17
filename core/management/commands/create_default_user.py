# core/management/commands/create_default_user.py
"""
Creates a default admin login on first run, if no users exist yet.

Used by the packaged desktop app so a fresh install has something to log
in with immediately. Safe to run every time -- it does nothing once any
user already exists.

Configure via environment variables (see .env.example):
    DEFAULT_USER_EMAIL
    DEFAULT_USER_PASSWORD
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a default superuser login if no users exist yet."

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.exists():
            self.stdout.write("A user already exists -- skipping default user creation.")
            return

        email = os.environ.get("DEFAULT_USER_EMAIL", "admin@example.com")
        password = os.environ.get("DEFAULT_USER_PASSWORD", "admin123")

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created default login -- email: {email}")
        )
