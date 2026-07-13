# crm/admin.py
from django.contrib import admin
from .models import Contact, Interaction, FollowUpTemplate


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 1
    fields = ("date", "direction", "channel", "message", "image")
    ordering = ("-date",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "social_handle",
        "status",
        "project",
        "follow_up_1_done",
        "follow_up_2_done",
        "follow_up_3_done",
        "joined_email_list",
        "made_purchase",
        "revenue",
        "follow_up_date",
    )
    list_filter = (
        "platform",
        "status",
        "project",
        "joined_email_list",
        "made_purchase",
        "follow_up_1_done",
        "follow_up_2_done",
        "follow_up_3_done",
    )
    list_editable = ("joined_email_list", "made_purchase")
    list_select_related = ("project",)
    search_fields = ("name", "social_handle", "email", "tags", "notes")
    date_hierarchy = "created_at"
    inlines = [InteractionInline]


@admin.register(FollowUpTemplate)
class FollowUpTemplateAdmin(admin.ModelAdmin):
    list_display = ("stage", "message")


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("contact", "date", "direction", "channel")
    list_filter = ("direction", "channel", "date")
    search_fields = ("contact__name", "message")
    date_hierarchy = "date"
