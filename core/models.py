# core/models.py
from django.db import models

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SiteConfiguration(models.Model):
    """
    Single site configuration for managing site-wide settings.
    Uses Django's singleton pattern with the default manager.
    """
    site_name = models.CharField(max_length=100, default="Project Tracker")
    site_description = models.TextField(blank=True, default="A tool for tracking your projects and tasks")
    contact_email = models.EmailField(blank=True)
    enable_work_timer = models.BooleanField(default=True)
    maintenance_mode = models.BooleanField(default=False)
    
    # Add social media links
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Add branding
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    default_og_image = models.ImageField(upload_to='site/', blank=True, null=True, 
                                     help_text="Default image for social media sharing (1200x630px recommended)")

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # This ensures we only ever have one instance
        self.pk = 1
        super().save(*args, **kwargs)
        