# projects/models.py
from datetime import timedelta

from django.db import models
from django.utils import timezone


class Project(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_worked_on = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=1)  # 1 = highest

    def __str__(self):
        return self.name

    def mark_as_worked_on(self):
        self.last_worked_on = timezone.now()
        self.save()


class Task(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In progress"),
        ("done", "Done"),
    ]

    RECURRENCE_CHOICES = [
        ("none", "One-off"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    # Legacy flag kept in sync with status ("done") so existing templates keep working.
    is_completed = models.BooleanField(default=False)
    scheduled_date = models.DateField(
        null=True, blank=True, help_text="The day you plan to do this task"
    )
    estimate_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Rough time estimate, for planning your week"
    )
    recurrence = models.CharField(
        max_length=10,
        choices=RECURRENCE_CHOICES,
        default="none",
        blank=True,
        help_text="A habit that repeats. Completion is tracked per day/week/month instead of once.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["order", "created_at"]

    def save(self, *args, **kwargs):
        # `status` is the source of truth; keep the legacy is_completed flag derived from it.
        self.is_completed = self.status == "done"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        from django.utils import timezone

        return (
            self.scheduled_date is not None
            and self.status != "done"
            and self.scheduled_date < timezone.localdate()
        )

    @property
    def is_habit(self):
        return self.recurrence != "none"

    def current_period_start(self, today=None):
        """The key used to track this habit's completion for 'now' (today's day/week/month)."""
        today = today or timezone.localdate()
        if self.recurrence == "daily":
            return today
        if self.recurrence == "weekly":
            return today - timedelta(days=today.weekday())  # Monday
        if self.recurrence == "monthly":
            return today.replace(day=1)
        return today

    def is_done_for_current_period(self, today=None):
        if not self.is_habit:
            return self.status == "done"
        period = self.current_period_start(today)
        return self.completions.filter(period_start=period).exists()

    def toggle_current_period(self, today=None):
        """Mark/unmark this habit done for the current day/week/month. Returns new done state."""
        period = self.current_period_start(today)
        existing = self.completions.filter(period_start=period).first()
        if existing:
            existing.delete()
            return False
        self.completions.create(period_start=period)
        return True


class TaskCompletion(models.Model):
    """One record per period (day/week/month) a recurring Task was marked done."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="completions")
    period_start = models.DateField(help_text="Day, Monday-of-week, or 1st-of-month this completion covers")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("task", "period_start")
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.task.title} @ {self.period_start}"


class WorkSession(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="work_sessions"
    )
    task = models.ForeignKey(
        "Task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="work_sessions",
        help_text="Optional: the specific task this work was against",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def duration_minutes(self):
        if not self.end_time:
            return 0
        duration = self.end_time - self.start_time
        return duration.total_seconds() // 60
