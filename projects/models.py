# projects/models.py
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
