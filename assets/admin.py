# assets/admin.py
from django.contrib import admin

from .models import Asset, GenerationJob, PromptTemplate, VoiceProfile


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("title", "file_type", "project", "contact", "token_count", "updated_at")
    list_filter = ("file_type", "project")
    search_fields = ("title", "content", "tags")
    date_hierarchy = "created_at"


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "content_type", "is_active", "updated_at")
    list_filter = ("content_type", "is_active")
    search_fields = ("name", "system_prompt")


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sentence_length", "updated_at")
    list_filter = ("is_active", "sentence_length")
    filter_horizontal = ("source_assets",)


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "prompt_template", "voice_profile", "status", "result_page", "created_at")
    list_filter = ("status", "prompt_template")
    readonly_fields = ("created_at", "completed_at")
