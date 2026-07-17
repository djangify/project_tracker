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

    # AI generation (assets app) — entered here rather than as an
    # environment variable so it works the same way in the packaged
    # desktop app as it does in dev, and so it's editable without touching
    # a config file. Stored in your local database only — never sent
    # anywhere except directly to whichever provider you choose below,
    # when you generate content.
    AI_PROVIDER_CHOICES = [
        ("anthropic", "Anthropic (Claude)"),
        ("openai", "OpenAI (ChatGPT)"),
        ("gemini", "Google (Gemini)"),
    ]
    ai_provider = models.CharField(
        max_length=20,
        choices=AI_PROVIDER_CHOICES,
        default="anthropic",
        help_text="Which AI provider your API key below is for.",
    )
    ai_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Your API key for the provider selected above. Leave blank to disable AI content generation.",
    )
    ai_model = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional. Leave blank to use a sensible default for the selected provider.",
    )

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # This ensures we only ever have one instance
        self.pk = 1
        super().save(*args, **kwargs)
        