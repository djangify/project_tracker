# core/admin.py
from django.contrib import admin
from adminita.utils import AlwaysVisibleAdmin
from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(AlwaysVisibleAdmin):
    list_display = ["site_name"]
    list_display_links = ["site_name"]

    fieldsets = (
        (
            "Site Details",
            {"fields": ("site_name", "site_description", "contact_email")},
        ),
        ("Features", {"fields": ("enable_work_timer", "maintenance_mode")}),
        (
            "Social Media",
            {"fields": ("twitter_url", "linkedin_url", "github_url", "facebook_url")},
        ),
        ("Branding", {"fields": ("logo", "favicon", "default_og_image")}),
    )

    # ALWAYS allow viewing and editing the single record
    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    # Allow adding only if none exists
    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    # DO NOT block delete — Django admin breaks if you do
    def has_delete_permission(self, request, obj=None):
        return True
