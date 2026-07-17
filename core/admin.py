from django import forms
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "ai_api_key":
            # Masked like a password field, but pre-filled so re-saving the
            # form doesn't blank out an already-set key.
            field.widget = forms.PasswordInput(render_value=True, attrs=field.widget.attrs)
        return field

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
        (
            "AI Generation",
            {"fields": ("ai_provider", "ai_api_key", "ai_model")},
        ),
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
