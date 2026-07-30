# ai_settings/migrations/0002_migrate_key_from_siteconfig.py
"""One-time move of the AI provider/key/model from core.SiteConfiguration (the
old plaintext Settings page) into the encrypted AIProviderConfig, so there's a
single AI config. Non-destructive: SiteConfiguration keeps its values; this only
seeds AIProviderConfig if nothing is active yet."""
from django.db import migrations


def migrate_key(apps, schema_editor):
    SiteConfiguration = apps.get_model("core", "SiteConfiguration")
    AIProviderConfig = apps.get_model("ai_settings", "AIProviderConfig")
    from ai_settings.encryption import encrypt

    sc = SiteConfiguration.objects.filter(pk=1).first()
    if not sc or not getattr(sc, "ai_api_key", ""):
        return
    # Respect an already-configured active provider.
    if AIProviderConfig.objects.filter(is_active=True).exists():
        return

    provider = sc.ai_provider or "anthropic"
    if provider not in ("openai", "anthropic", "gemini"):
        return

    obj, _ = AIProviderConfig.objects.get_or_create(provider=provider)
    obj.api_key_encrypted = encrypt(sc.ai_api_key)
    obj.model_name = sc.ai_model or ""
    obj.is_active = True
    obj.save()
    AIProviderConfig.objects.exclude(pk=obj.pk).update(is_active=False)


def noop(apps, schema_editor):
    # Non-reversible seed; nothing to undo (SiteConfiguration is untouched).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("ai_settings", "0001_initial"),
        ("core", "0004_remove_siteconfiguration_anthropic_api_key_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_key, noop),
    ]
