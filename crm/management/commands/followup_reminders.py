# crm/management/commands/followup_reminders.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from crm.models import Contact


class Command(BaseCommand):
    help = "Email a reminder listing CRM follow-ups that are due or overdue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--always",
            action="store_true",
            help="Send the email even when nothing is due (default: skip).",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        due = (
            Contact.objects.filter(
                follow_up_date__isnull=False,
                follow_up_date__lte=today,
                follow_up_3_done=False,
            )
            .order_by("follow_up_date")
        )
        count = due.count()
        domain = (getattr(settings, "PRIMARY_DOMAIN", "") or "").rstrip("/")

        if count == 0 and not options["always"]:
            self.stdout.write("No follow-ups due today — no email sent.")
            return

        if count == 0:
            subject = "CRM follow-ups: nothing due today"
            body = "No follow-ups are due today. Nice work staying on top of it!"
        else:
            lines = []
            for c in due:
                overdue = " (OVERDUE)" if c.follow_up_date < today else ""
                link = f"{domain}/crm/contact/{c.pk}/" if domain else ""
                lines.append(
                    f"- {c.name} — Follow-up {c.current_stage} "
                    f"due {c.follow_up_date:%b %d}{overdue}  {link}"
                )
            plural = "" if count == 1 else "s"
            subject = f"CRM follow-ups: {count} due today"
            body = (
                f"You have {count} follow-up{plural} due:\n\n"
                + "\n".join(lines)
                + (f"\n\nSee all: {domain}/crm/follow-ups/" if domain else "")
            )

        recipient = getattr(settings, "FOLLOWUP_REMINDER_TO", None)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not recipient:
            self.stderr.write("FOLLOWUP_REMINDER_TO is not set; cannot send.")
            return

        send_mail(subject, body, from_email, [recipient], fail_silently=False)
        self.stdout.write(
            self.style.SUCCESS(f"Reminder sent to {recipient} ({count} due).")
        )
