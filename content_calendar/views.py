# content_calendar/views.py
import calendar
import json
from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView, View
from rest_framework import viewsets

from projects.models import Project

from .forms import ContentItemForm
from .models import ContentItem, Platform
from .serializers import ContentItemSerializer, PlatformSerializer


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------
class ContentItemViewSet(viewsets.ModelViewSet):
    queryset = ContentItem.objects.all()
    serializer_class = ContentItemSerializer


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


# ---------------------------------------------------------------------------
# Content views: Table / Board / Calendar — all filter by ?project=<id>
# (cloned from projects.views._TaskViewMixin and friends)
# ---------------------------------------------------------------------------
class _ContentViewMixin(LoginRequiredMixin):
    def get_current_project(self):
        pid = self.request.GET.get("project")
        if pid and pid.isdigit():
            return Project.objects.filter(pk=pid).first()
        return None

    def get_items(self):
        qs = ContentItem.objects.select_related("project").prefetch_related("platforms")
        project = self.get_current_project()
        if project:
            qs = qs.filter(project=project)
        return qs

    def base_context(self, view_name):
        project = self.get_current_project()
        return {
            "projects": Project.objects.all().order_by("name"),
            "current_project": project,
            "current_project_id": str(project.id) if project else "",
            "view": view_name,
        }


class ContentTableView(_ContentViewMixin, TemplateView):
    template_name = "content_calendar/content/table.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context("table"))
        items = self.get_items().order_by("scheduled_date", "order")
        ctx["items"] = items
        ctx["status_choices"] = ContentItem.STATUS_CHOICES
        ctx["approval_choices"] = ContentItem.APPROVAL_STATUS_CHOICES
        return ctx


class ContentBoardView(_ContentViewMixin, TemplateView):
    """Board grouped by approval status, so items can be reviewed/approved here."""

    template_name = "content_calendar/content/board.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context("board"))
        items = list(self.get_items().order_by("scheduled_date", "order"))
        ctx["columns"] = [
            {"key": key, "label": label,
             "items": [i for i in items if i.approval_status == key]}
            for key, label in ContentItem.APPROVAL_STATUS_CHOICES
        ]
        ctx["approval_choices"] = ContentItem.APPROVAL_STATUS_CHOICES
        return ctx


class ContentCalendarView(_ContentViewMixin, TemplateView):
    template_name = "content_calendar/content/calendar.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.base_context("calendar"))
        today = timezone.localdate()

        try:
            year, month = map(int, self.request.GET.get("month", "").split("-"))
            first = date(year, month, 1)
        except (ValueError, AttributeError):
            first = today.replace(day=1)

        last_day = calendar.monthrange(first.year, first.month)[1]
        month_end = first.replace(day=last_day)

        by_day = defaultdict(list)
        for item in self.get_items().filter(scheduled_date__range=(first, month_end)):
            by_day[item.scheduled_date].append(item)

        cal = calendar.Calendar(firstweekday=0)  # Monday
        weeks = []
        for week in cal.monthdatescalendar(first.year, first.month):
            days = []
            for d in week:
                days.append({
                    "date": d,
                    "in_month": d.month == first.month,
                    "is_today": d == today,
                    "items": by_day.get(d, []),
                })
            weeks.append(days)

        ctx["weeks"] = weeks
        ctx["month_label"] = first.strftime("%B %Y")
        ctx["prev_month"] = (first - timedelta(days=1)).replace(day=1).strftime("%Y-%m")
        ctx["next_month"] = (month_end + timedelta(days=1)).strftime("%Y-%m")
        return ctx


# ---------------------------------------------------------------------------
# Create / edit / delete (UI CRUD alongside the admin)
# ---------------------------------------------------------------------------
class ContentItemCreateView(LoginRequiredMixin, CreateView):
    model = ContentItem
    form_class = ContentItemForm
    template_name = "content_calendar/content/content_form.html"
    success_url = reverse_lazy("content_calendar:content_calendar")

    def get_initial(self):
        initial = super().get_initial()
        d = self.request.GET.get("date")
        if d:
            initial["scheduled_date"] = d
        pid = self.request.GET.get("project")
        if pid and pid.isdigit():
            initial["project"] = pid
        return initial


class ContentItemUpdateView(LoginRequiredMixin, UpdateView):
    model = ContentItem
    form_class = ContentItemForm
    template_name = "content_calendar/content/content_form.html"

    def get_success_url(self):
        return reverse("content_calendar:content_table")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["editing"] = True
        return ctx


class ContentItemDeleteView(LoginRequiredMixin, DeleteView):
    model = ContentItem
    template_name = "content_calendar/content/content_confirm_delete.html"
    success_url = reverse_lazy("content_calendar:content_table")


class ContentItemSetApprovalView(LoginRequiredMixin, View):
    """Set an item's approval status (for the board select). JSON or form 'status'."""

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(ContentItem, pk=kwargs["pk"])
        status = request.POST.get("status")
        if status is None:
            try:
                status = json.loads(request.body or "{}").get("status")
            except json.JSONDecodeError:
                status = None
        if status in dict(ContentItem.APPROVAL_STATUS_CHOICES):
            item.approval_status = status
            item.save(update_fields=["approval_status", "updated_at"])
            return JsonResponse({"approval_status": item.approval_status})
        return JsonResponse({"error": "invalid status"}, status=400)
