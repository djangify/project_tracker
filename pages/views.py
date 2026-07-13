# pages/views.py
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import DetailView, ListView

from crm.models import Contact
from projects.models import Project

from .models import Page


@method_decorator(ensure_csrf_cookie, name="dispatch")
class PageDetailView(LoginRequiredMixin, DetailView):
    """The one page view — it's single-user, so it's always editable."""

    model = Page
    template_name = "pages/page_detail.html"
    context_object_name = "page"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ancestors"] = self.object.ancestors()
        ctx["child_pages"] = self.object.visible_children()
        ctx["all_projects"] = Project.objects.all()
        ctx["all_contacts"] = Contact.objects.all()
        return ctx


class PageCreateView(LoginRequiredMixin, View):
    """Create a blank page, optionally under ?parent= / linked to ?project= / ?contact=."""

    def post(self, request, *args, **kwargs):
        def _param(key):
            return request.GET.get(key) or request.POST.get(key)

        page = Page()
        parent_id = _param("parent")
        if parent_id:
            page.parent = get_object_or_404(Page, pk=parent_id)
        project_id = _param("project")
        if project_id:
            page.project = get_object_or_404(Project, pk=project_id)
        contact_id = _param("contact")
        if contact_id:
            page.contact = get_object_or_404(Contact, pk=contact_id)
        page.save()
        return redirect(page.get_absolute_url())


class PageContentUpdateView(LoginRequiredMixin, View):
    """Autosave endpoint. Accepts JSON {title, icon, content}; returns {updated_at}."""

    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs["pk"])
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if "title" in data:
            title = (data["title"] or "").strip()
            page.title = title or "Untitled"
        if "icon" in data:
            page.icon = (data["icon"] or "")[:8]
        if "content" in data:
            page.content = data["content"]
        if "project" in data:
            page.project = (
                Project.objects.filter(pk=data["project"]).first()
                if data["project"]
                else None
            )
        if "contact" in data:
            page.contact = (
                Contact.objects.filter(pk=data["contact"]).first()
                if data["contact"]
                else None
            )
        page.save()
        return JsonResponse(
            {"updated_at": page.updated_at.isoformat(), "title": page.title}
        )


class PageFavoriteToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs["pk"])
        page.is_favorite = not page.is_favorite
        page.save(update_fields=["is_favorite", "updated_at"])
        return JsonResponse({"is_favorite": page.is_favorite})


class PageArchiveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs["pk"])
        page.is_archived = True
        page.save(update_fields=["is_archived", "updated_at"])
        if page.parent:
            return redirect(page.parent.get_absolute_url())
        return redirect("pages:trash")


class PageRestoreView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs["pk"])
        page.is_archived = False
        page.save(update_fields=["is_archived", "updated_at"])
        return redirect(page.get_absolute_url())


class PageDeleteView(LoginRequiredMixin, View):
    """Hard delete — only reachable from Trash."""

    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=kwargs["pk"])
        page.delete()
        return redirect("pages:trash")


class TrashView(LoginRequiredMixin, ListView):
    template_name = "pages/trash.html"
    context_object_name = "pages"

    def get_queryset(self):
        return Page.objects.filter(is_archived=True).order_by("-updated_at")
