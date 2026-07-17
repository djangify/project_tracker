# sequences/models.py
from django.db import models


class EmailSequence(models.Model):
    """A named nurture sequence, e.g. 'Welcome series' or 'Post-purchase'.
    Targets contacts on your email list (crm.Contact.joined_email_list=True),
    not the 1:1 follow-ups already handled by crm.FollowUpTemplate."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Email sequences"

    def __str__(self):
        return self.name


class EmailStep(models.Model):
    """One email in a sequence, sent `delay_days` after enrollment (or after
    the previous step, at your discretion when running it)."""

    sequence = models.ForeignKey(EmailSequence, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField(default=0)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="Plain text or simple HTML")
    delay_days = models.PositiveIntegerField(default=0, help_text="Days after enrollment to send this step")

    class Meta:
        ordering = ["sequence", "order"]

    def __str__(self):
        return f"{self.sequence.name} — step {self.order}: {self.subject}"


class SequenceEnrollment(models.Model):
    """Tracks which contact is on which sequence and how far they've gotten,
    so a step never gets sent to the same contact twice."""

    sequence = models.ForeignKey(EmailSequence, on_delete=models.CASCADE, related_name="enrollments")
    contact = models.ForeignKey("crm.Contact", on_delete=models.CASCADE, related_name="sequence_enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_step_sent = models.ForeignKey(
        EmailStep, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("sequence", "contact")
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.contact.name} on {self.sequence.name}"
