# Backfill Task.status from the legacy is_completed flag.
from django.db import migrations


def set_status_from_is_completed(apps, schema_editor):
    Task = apps.get_model("projects", "Task")
    Task.objects.filter(is_completed=True).update(status="done")
    Task.objects.filter(is_completed=False).update(status="planned")


def reverse(apps, schema_editor):
    # is_completed is still populated, so nothing to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_task_estimate_minutes_task_scheduled_date_and_more'),
    ]

    operations = [
        migrations.RunPython(set_status_from_is_completed, reverse),
    ]
