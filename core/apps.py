# core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Create site configuration if it doesn't exist
        """
        # Only import and run this code when Django is ready
        # to avoid AppRegistryNotReady exception
        try:
            from .models import SiteConfiguration
            SiteConfiguration.objects.get_or_create(pk=1)
        except:
            # If there's an error (e.g., table doesn't exist yet),
            # just pass - it will be created after migrations
            pass
        