# ai_settings/models.py
from django.db import models

from .encryption import decrypt, encrypt


class AIProviderConfig(models.Model):
    """One row per AI provider. `is_active` marks which one every AI feature
    (generation engine, chat assistant, MCP tools) routes through. The API key
    is encrypted at rest — see ai_settings.encryption.
    """

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic (Claude)"),
        ("gemini", "Google Gemini"),
    ]

    # Sensible current defaults, shown as the model_name placeholder per provider.
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-5",
        "gemini": "gemini-2.0-flash",
    }

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, unique=True)
    # Encrypted at rest; never store the plaintext key. Access via the `api_key`
    # property below, which transparently encrypts/decrypts.
    api_key_encrypted = models.TextField(blank=True, default="")
    model_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI provider config"
        verbose_name_plural = "AI provider configs"
        ordering = ["provider"]

    def __str__(self):
        active = " (active)" if self.is_active else ""
        return f"{self.get_provider_display()}{active}"

    # -- API key: encrypt on set, decrypt on get -----------------------------
    @property
    def api_key(self) -> str:
        return decrypt(self.api_key_encrypted)

    @api_key.setter
    def api_key(self, value: str):
        self.api_key_encrypted = encrypt(value or "")

    @property
    def has_key(self) -> bool:
        return bool(self.api_key_encrypted)

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODELS.get(self.provider, "")

    @property
    def effective_model(self) -> str:
        return self.model_name or self.default_model

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Only one provider active at a time.
        if self.is_active:
            AIProviderConfig.objects.exclude(pk=self.pk).filter(is_active=True).update(
                is_active=False
            )

    @classmethod
    def active(cls):
        """Return the active provider config, or None."""
        return cls.objects.filter(is_active=True).first()
