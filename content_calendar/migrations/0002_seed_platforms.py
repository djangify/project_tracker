# content_calendar/migrations/0002_seed_platforms.py
from django.db import migrations

PLATFORMS = [
    ("TikTok", 1),
    ("Instagram", 2),
    ("Pinterest", 3),
    ("Facebook", 4),
    ("YouTube", 5),
    ("WhatsApp", 6),
]


def seed_platforms(apps, schema_editor):
    Platform = apps.get_model("content_calendar", "Platform")
    for name, order in PLATFORMS:
        Platform.objects.get_or_create(name=name, defaults={"order": order})


def unseed_platforms(apps, schema_editor):
    Platform = apps.get_model("content_calendar", "Platform")
    Platform.objects.filter(name__in=[p[0] for p in PLATFORMS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content_calendar", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_platforms, unseed_platforms),
    ]
