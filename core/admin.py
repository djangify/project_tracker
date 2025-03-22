# core/admin.py
from django.contrib import admin
from .models import SiteConfiguration

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Details', {
            'fields': ('site_name', 'site_description', 'contact_email')
        }),
        ('Features', {
            'fields': ('enable_work_timer', 'maintenance_mode')
        }),
        ('Social Media', {
            'fields': ('twitter_url', 'linkedin_url', 'github_url', 'facebook_url')
        }),
        ('Branding', {
            'fields': ('logo', 'favicon', 'default_og_image')
        }),
    )
    
    def has_add_permission(self, request):
        # Check if an instance already exists
        return SiteConfiguration.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the configuration
        return False
    