# core/management/commands/daily_reminder.py
"""
Email a reminder of what's still open for today: one-off tasks scheduled for
today (plus anything overdue) and any recurring habit not yet marked done for
its current day/week/month.

Meant to run once a day, late afternoon/evening, via cron:
    0 18 * * * cd /path/to/tracker && venv/bin/python manage.py daily_reminder
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from projects.models import Task

OPEN_STATUSES = ["planned", "in_progress"]


class Command(BaseCommand):
    help = "Email a reminder listing today's incomplete tasks and undone habits."

    def add_arguments(self, parser):
        parser.add_argument(
            "--always",
            action="store_true",
            help="Send the email even when everything is done (default: skip).",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        domain = (getattr(settings, "PRIMARY_DOMAIN", "") or "").rstrip("/")

        overdue = (
            Task.objects.filter(status__in=OPEN_STATUSES, scheduled_date__lt=today)
            .select_related("project")
            .order_by("scheduled_date")
        )
        today_tasks = (
            Task.objects.filter(status__in=OPEN_STATUSES, scheduled_date=today)
            .select_related("project")
        )
        habits = Task.objects.exclude(recurrence="none").select_related("project")
        undone_habits = [h for h in habits if not h.is_done_for_current_period(today)]

        total = overdue.count() + today_tasks.count() + len(undone_habits)

        if total == 0 and not options["always"]:
            self.stdout.write("Nothing outstanding — no email sent.")
            return

        if total == 0:
            subject = "Today: all clear"
            body = "Everything scheduled for today, and every habit, is marked done. Nice work."
        else:
            lines = []

            if overdue:
                lines.append("OVERDUE")
                for t in overdue:
                    lines.append(f"- {t.title} ({t.project.name}) — was due {t.scheduled_date:%b %d}")
                lines.append("")

            if today_tasks:
                lines.append("SCHEDULED TODAY")
                for t in today_tasks:
                    lines.append(f"- {t.title} ({t.project.name})")
                lines.append("")

            if undone_habits:
                lines.append("HABITS NOT YET DONE")
                for h in undone_habits:
                    lines.append(f"- [{h.get_recurrence_display()}] {h.title} ({h.project.name})")
                lines.append("")

            plural = "" if total == 1 else "s"
            subject = f"Today: {total} thing{plural} still open"
            body = "\n".join(lines).rstrip()
            if domain:
                body += f"\n\nOpen the dashboard: {domain}/"

        recipient = getattr(settings, "DAILY_REMINDER_TO", None) or getattr(
            settings, "FOLLOWUP_REMINDER_TO", None
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not recipient:
            self.stderr.write("DAILY_REMINDER_TO is not set; cannot send.")
            return

        send_mail(subject, body, from_email, [recipient], fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f"Reminder sent to {recipient} ({total} open)."))
