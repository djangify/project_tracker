# pages/admin.py
from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "parent", "is_favorite", "is_archived", "updated_at")
    list_filter = ("is_favorite", "is_archived")
    search_fields = ("title",)
    raw_id_fields = ("parent", "project", "contact")
    readonly_fields = ("created_at", "updated_at")
