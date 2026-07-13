# crm/views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.db.models import Q, Sum
from rest_framework import viewsets

from .models import Contact, Interaction, FollowUpTemplate
from .serializers import ContactSerializer, InteractionSerializer

# Days to wait before the next follow-up stage
FOLLOW_UP_GAP_DAYS = 2


# ---------------------------------------------------------------------------
# Frontend views
# ---------------------------------------------------------------------------
class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "crm/contact_list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        qs = Contact.objects.all()
        status = self.request.GET.get("status")
        platform = self.request.GET.get("platform")
        search = self.request.GET.get("q")

        if status and status != "all":
            qs = qs.filter(status=status)
        if platform and platform != "all":
            qs = qs.filter(platform=platform)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(social_handle__icontains=search)
                | Q(email__icontains=search)
                | Q(tags__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Contact.STATUS_CHOICES
        context["platform_choices"] = Contact.PLATFORM_CHOICES
        context["current_status"] = self.request.GET.get("status", "all")
        context["current_platform"] = self.request.GET.get("platform", "all")
        context["search"] = self.request.GET.get("q", "")

        # Dashboard totals (always across ALL contacts, ignoring filters)
        messages_sent = Interaction.objects.filter(direction="outbound").count()
        responses = Interaction.objects.filter(direction="inbound").count()
        context["stats"] = {
            "messages_sent": messages_sent,
            "responses": responses,
            "response_rate": round(responses / messages_sent * 100) if messages_sent else 0,
            "list_signups": Contact.objects.filter(joined_email_list=True).count(),
            "sales": Contact.objects.filter(made_purchase=True).count(),
            "revenue": Contact.objects.filter(made_purchase=True).aggregate(
                total=Sum("revenue")
            )["total"] or 0,
        }
        return context


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = "crm/contact_detail.html"
    context_object_name = "contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.object
        # Build the three stages with their done-state for the template
        context["stages"] = [
            {"num": 1, "done": contact.follow_up_1_done},
            {"num": 2, "done": contact.follow_up_2_done},
            {"num": 3, "done": contact.follow_up_3_done},
        ]
        # Suggested message template for the next incomplete stage
        if contact.current_stage:
            context["suggested_template"] = FollowUpTemplate.objects.filter(
                stage=contact.current_stage
            ).first()
        return context


CONTACT_FIELDS = [
    "name",
    "platform",
    "social_handle",
    "profile_url",
    "email",
    "status",
    "project",
    "tags",
    "follow_up_date",
    "joined_email_list",
    "made_purchase",
    "revenue",
    "notes",
]

STAGE_FIELDS = ["follow_up_1_done", "follow_up_2_done", "follow_up_3_done"]


class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    fields = CONTACT_FIELDS
    template_name = "crm/contact_form.html"

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.object.pk})


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    fields = CONTACT_FIELDS + STAGE_FIELDS
    template_name = "crm/contact_form.html"

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.object.pk})


class InteractionCreateView(LoginRequiredMixin, CreateView):
    model = Interaction
    fields = ["date", "direction", "channel", "message", "image"]
    template_name = "crm/interaction_form.html"

    def form_valid(self, form):
        contact = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        form.instance.contact = contact
        # Logging a touch nudges the contact forward from "new"
        if contact.status == "new":
            contact.status = "contacted"
            contact.save(update_fields=["status"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.kwargs["contact_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        return context


class FollowUpListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "crm/followups.html"
    context_object_name = "contacts"

    def get_queryset(self):
        # Anyone with a follow-up date who still has an incomplete stage
        return Contact.objects.filter(
            follow_up_date__isnull=False,
            follow_up_3_done=False,
        ).order_by("follow_up_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.localdate()
        return context


class StageToggleView(LoginRequiredMixin, View):
    """
    Toggle a follow-up stage (1, 2 or 3) done/undone for a contact.
    When a stage is marked done, auto-schedule the next follow-up
    FOLLOW_UP_GAP_DAYS out (unless it was the final stage).
    """

    STAGE_FIELD = {1: "follow_up_1_done", 2: "follow_up_2_done", 3: "follow_up_3_done"}

    def post(self, request, *args, **kwargs):
        contact = get_object_or_404(Contact, pk=kwargs["pk"])
        stage = int(kwargs["stage"])
        field = self.STAGE_FIELD.get(stage)
        if field:
            new_value = not getattr(contact, field)
            setattr(contact, field, new_value)
            if new_value:
                # Just completed this stage — schedule the next one
                if not contact.follow_ups_complete:
                    contact.follow_up_date = timezone.localdate() + timedelta(
                        days=FOLLOW_UP_GAP_DAYS
                    )
                else:
                    contact.follow_up_date = None
            contact.save()
        next_url = request.POST.get("next") or reverse(
            "crm:contact_detail", kwargs={"pk": contact.pk}
        )
        return HttpResponseRedirect(next_url)


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------
class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
