# ai_settings/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import ai_client
from .encryption import decrypt, encrypt
from .models import AIProviderConfig


class EncryptionTests(TestCase):
    def test_round_trip(self):
        secret = "sk-test-1234567890"
        token = encrypt(secret)
        self.assertNotEqual(token, secret)
        self.assertEqual(decrypt(token), secret)

    def test_empty_values(self):
        self.assertEqual(encrypt(""), "")
        self.assertEqual(decrypt(""), "")

    def test_decrypt_garbage_returns_empty(self):
        self.assertEqual(decrypt("not-a-valid-token"), "")


class AIProviderConfigTests(TestCase):
    def test_api_key_encrypted_at_rest(self):
        config = AIProviderConfig(provider="openai")
        config.api_key = "sk-secret"
        config.save()
        # The stored column is not the plaintext.
        self.assertNotIn("sk-secret", config.api_key_encrypted)
        # But the property decrypts it back.
        config.refresh_from_db()
        self.assertEqual(config.api_key, "sk-secret")
        self.assertTrue(config.has_key)

    def test_only_one_active(self):
        a = AIProviderConfig.objects.create(provider="openai", is_active=True)
        b = AIProviderConfig.objects.create(provider="anthropic", is_active=True)
        a.refresh_from_db()
        self.assertFalse(a.is_active)
        self.assertTrue(b.is_active)
        self.assertEqual(AIProviderConfig.active(), b)

    def test_effective_model_falls_back_to_default(self):
        config = AIProviderConfig.objects.create(provider="gemini")
        self.assertEqual(config.effective_model, config.default_model)
        config.model_name = "gemini-custom"
        self.assertEqual(config.effective_model, "gemini-custom")


class AIClientTests(TestCase):
    def test_generate_raises_without_active_provider(self):
        with self.assertRaises(ai_client.AIConfigError):
            ai_client.generate("sys", "hi")

    def test_generate_raises_without_key(self):
        AIProviderConfig.objects.create(provider="openai", is_active=True)
        with self.assertRaises(ai_client.AIConfigError):
            ai_client.generate("sys", "hi")


class AISettingsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="tester", password="pw12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_settings_page_creates_rows(self):
        resp = self.client.get(reverse("ai_settings:settings"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AIProviderConfig.objects.count(), 3)

    def test_save_sets_key_and_active(self):
        self.client.get(reverse("ai_settings:settings"))  # create rows
        resp = self.client.post(reverse("ai_settings:settings"), data={
            "active_provider": "anthropic",
            "api_key_anthropic": "sk-ant-xyz",
            "model_name_anthropic": "claude-custom",
            "api_key_openai": "",
            "model_name_openai": "",
            "api_key_gemini": "",
            "model_name_gemini": "",
        })
        self.assertEqual(resp.status_code, 302)
        anthropic = AIProviderConfig.objects.get(provider="anthropic")
        self.assertTrue(anthropic.is_active)
        self.assertEqual(anthropic.api_key, "sk-ant-xyz")
        self.assertEqual(anthropic.model_name, "claude-custom")

    def test_blank_key_preserves_existing(self):
        self.client.get(reverse("ai_settings:settings"))
        openai = AIProviderConfig.objects.get(provider="openai")
        openai.api_key = "sk-original"
        openai.save()
        self.client.post(reverse("ai_settings:settings"), data={
            "active_provider": "openai",
            "api_key_openai": "",  # blank = keep
            "model_name_openai": "",
            "api_key_anthropic": "",
            "model_name_anthropic": "",
            "api_key_gemini": "",
            "model_name_gemini": "",
        })
        openai.refresh_from_db()
        self.assertEqual(openai.api_key, "sk-original")

    def test_test_connection_reports_config_error(self):
        resp = self.client.post(reverse("ai_settings:test_connection"))
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("ai_settings:settings"))
        self.assertEqual(resp.status_code, 302)
