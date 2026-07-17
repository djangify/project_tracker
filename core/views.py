# core/views.py
from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView, UpdateView

from projects.models import Project, Task, WorkSession
from .models import SiteConfiguration
from .utils import format_duration

OPEN_STATUSES = ["planned", "in_progress"]


@method_decorator(ensure_csrf_cookie, name="dispatch")
class DashboardView(LoginRequiredMixin, TemplateView):
    """Cross-business overview: Today, My Week, All Tasks, Work Log."""

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)

        open_tasks = Task.objects.filter(status__in=OPEN_STATUSES).select_related("project")

        # --- Panel 0: Habits (recurring tasks, tracked per day/week/month) ---
        habits = (
            Task.objects.exclude(recurrence="none")
            .select_related("project")
            .order_by("recurrence", "project__name")
        )
        for h in habits:
            h.done_now = h.is_done_for_current_period(today)
        ctx["habits"] = habits
        # Not-yet-done habits also surface in the Today panel, so they land in
        # the actual daily to-do list rather than only living in a separate section.
        ctx["today_habits"] = [h for h in habits if not h.done_now]

        # --- Panel 1: Today ---
        ctx["today"] = today
        ctx["today_tasks"] = open_tasks.filter(scheduled_date=today).order_by("project__name")
        ctx["overdue_tasks"] = open_tasks.filter(scheduled_date__lt=today).order_by(
            "scheduled_date", "project__name"
        )

        # --- Panel 2: My Week (clash = 2+ projects on one day) ---
        week_tasks = (
            Task.objects.filter(scheduled_date__range=(week_start, week_end))
            .select_related("project")
            .order_by("scheduled_date", "project__name")
        )
        days = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            day_tasks = [t for t in week_tasks if t.scheduled_date == d]
            project_ids = {t.project_id for t in day_tasks}
            days.append(
                {
                    "date": d,
                    "tasks": day_tasks,
                    "is_today": d == today,
                    "clash": len(project_ids) >= 2,
                    "project_count": len(project_ids),
                }
            )
        ctx["week_days"] = days

        # --- Panel 3: All Tasks (open, grouped by project) ---
        grouped = defaultdict(list)
        for t in open_tasks.order_by("project__name", "scheduled_date", "order"):
            grouped[t.project].append(t)
        ctx["tasks_by_project"] = sorted(
            grouped.items(), key=lambda kv: kv[0].name.lower()
        )

        # --- Panel 4: Work Log (this week) ---
        sessions = (
            WorkSession.objects.filter(
                start_time__date__range=(week_start, week_end)
            )
            .select_related("project", "task")
            .order_by("-start_time")
        )
        totals = defaultdict(int)
        for s in sessions:
            totals[s.project] += int(s.duration_minutes())
        total_minutes = sum(totals.values())
        ctx["work_sessions"] = sessions[:15]
        ctx["work_total_label"] = format_duration(total_minutes) if total_minutes else "0m"
        ctx["work_bars"] = [
            {
                "project": p,
                "label": format_duration(m),
                "pct": round(m / total_minutes * 100) if total_minutes else 0,
            }
            for p, m in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        ]

        ctx["week_start"] = week_start
        ctx["week_end"] = week_end
        return ctx


class SettingsView(LoginRequiredMixin, UpdateView):
    """
    In-app settings page — the AI key lives here (not an environment
    variable) so it works identically in the packaged desktop app and in
    dev, and so it's editable without touching a config file.
    """

    model = SiteConfiguration
    template_name = "core/settings.html"
    fields = [
        "site_name",
        "site_description",
        "contact_email",
        "anthropic_api_key",
        "anthropic_default_model",
    ]
    success_url = reverse_lazy("core:settings")

    def get_object(self, queryset=None):
        obj, _ = SiteConfiguration.objects.get_or_create(pk=1)
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Settings saved.")
        return response
