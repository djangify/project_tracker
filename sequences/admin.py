# sequences/admin.py
from django.contrib import admin

from .models import EmailSequence, EmailStep, SequenceEnrollment


class EmailStepInline(admin.TabularInline):
    model = EmailStep
    extra = 1
    fields = ("order", "subject", "delay_days", "body")


@admin.register(EmailSequence)
class EmailSequenceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [EmailStepInline]


@admin.register(SequenceEnrollment)
class SequenceEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("contact", "sequence", "last_step_sent", "completed", "enrolled_at")
    list_filter = ("sequence", "completed")
    search_fields = ("contact__name",)
