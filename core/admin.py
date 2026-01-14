from django.contrib import admin
from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the SiteConfiguration singleton.
    Ensures the model:
    - Always appears in the admin sidebar
    - Can always be opened and edited
    - Only allows one instance
    """

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

    # Always allow viewing
    def has_view_permission(self, request, obj=None):
        return True

    # Always allow editing the singleton instance
    def has_change_permission(self, request, obj=None):
        return True

    # Allow adding only when no instance exists
    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    # Allow delete so Django admin does not break
    def has_delete_permission(self, request, obj=None):
        return True
