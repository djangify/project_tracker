# content_calendar/admin.py
from django.contrib import admin

from .models import ContentItem, Platform


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "scheduled_date", "content_type", "status",
        "approval_status", "project",
    )
    list_filter = ("status", "approval_status", "content_type", "platforms", "project", "scheduled_date")
    list_editable = ("status", "approval_status")
    search_fields = ("topic", "hook", "caption", "pillar")
    date_hierarchy = "scheduled_date"
    filter_horizontal = ("platforms",)
    fieldsets = (
        ("Planning", {
            "fields": ("project", "scheduled_date", "pillar", "content_type", "topic", "platforms"),
        }),
        ("Content", {
            "fields": ("hook", "caption", "call_to_action", "hashtags", "tags_links",
                       "audio_sound", "image_video_cover", "content_link"),
        }),
        ("Status", {
            "fields": ("status", "approval_status", "order"),
        }),
    )
