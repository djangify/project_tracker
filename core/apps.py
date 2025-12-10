# core/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_site_config(sender, **kwargs):
    from .models import SiteConfiguration
    SiteConfiguration.objects.get_or_create(pk=1)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        post_migrate.connect(create_site_config, sender=self)