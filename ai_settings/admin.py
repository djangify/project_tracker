# ai_settings/admin.py
from django.contrib import admin

from .models import AIProviderConfig


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "model_name", "is_active", "has_key", "updated_at")
    list_filter = ("provider", "is_active")
    # The API key is encrypted at rest and never shown in the admin; manage it
    # from the AI Settings page instead.
    readonly_fields = ("has_key", "created_at", "updated_at")
    fields = ("provider", "model_name", "is_active", "has_key", "created_at", "updated_at")

    @admin.display(boolean=True, description="API key set")
    def has_key(self, obj):
        return obj.has_key
