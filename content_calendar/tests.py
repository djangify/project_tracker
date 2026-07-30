# content_calendar/tests.py
import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import generation
from .models import (
    ContentItem,
    ContentTemplate,
    ContentTemplatePrompt,
    Platform,
    VoiceProfile,
)


class ContentCalendarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="tester", password="pw12345")
        # Instagram is already seeded by the data migration; reuse it.
        cls.instagram = Platform.objects.get(name="Instagram")

    def setUp(self):
        self.client.force_login(self.user)

    def test_platforms_seeded_by_migration(self):
        # The data migration ships the common platforms out of the box.
        self.assertTrue(Platform.objects.filter(name="TikTok").exists())
        self.assertTrue(Platform.objects.filter(name="YouTube").exists())

    def test_create_item_shows_on_calendar(self):
        item = ContentItem.objects.create(
            topic="Summer skincare tips",
            scheduled_date=date(2026, 8, 15),
            status="scheduled",
        )
        item.platforms.add(self.instagram)

        resp = self.client.get(reverse("content_calendar:content_calendar") + "?month=2026-08")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Summer skincare tips")

    def test_board_groups_by_approval_status(self):
        ContentItem.objects.create(topic="Ready one", approval_status="ready")
        ContentItem.objects.create(topic="Draft one", approval_status="draft")

        resp = self.client.get(reverse("content_calendar:content_board"))
        self.assertEqual(resp.status_code, 200)
        columns = {c["key"]: c for c in resp.context["columns"]}
        self.assertEqual(len(columns["ready"]["items"]), 1)
        self.assertEqual(len(columns["draft"]["items"]), 1)

    def test_set_approval_updates_item(self):
        item = ContentItem.objects.create(topic="Needs review", approval_status="ready")
        resp = self.client.post(
            reverse("content_calendar:content_set_approval", args=[item.pk]),
            data={"status": "approved"},
        )
        self.assertEqual(resp.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.approval_status, "approved")

    def test_set_approval_rejects_invalid(self):
        item = ContentItem.objects.create(topic="X", approval_status="ready")
        resp = self.client.post(
            reverse("content_calendar:content_set_approval", args=[item.pk]),
            data={"status": "bogus"},
        )
        self.assertEqual(resp.status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.approval_status, "ready")

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("content_calendar:content_table"))
        self.assertEqual(resp.status_code, 302)


class ExtractJsonTests(TestCase):
    def test_plain_json(self):
        self.assertEqual(generation._extract_json('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        raw = "Here you go:\n```json\n{\"a\": 2}\n```\nthanks"
        self.assertEqual(generation._extract_json(raw), {"a": 2})

    def test_embedded_json(self):
        self.assertEqual(generation._extract_json('noise {"a": 3} more'), {"a": 3})

    def test_garbage_returns_empty(self):
        self.assertEqual(generation._extract_json("no json here"), {})


class PromptEnhancerTests(TestCase):
    def test_build_returns_system_and_user(self):
        system, user = generation.PromptEnhancer.build("write a hook", content_type="social")
        self.assertIn("social media", system.lower())
        self.assertIn("write a hook", user)

    def test_voice_block_included_when_enabled(self):
        voice = VoiceProfile.get_solo()
        voice.summary = "warm and direct"
        voice.tone_words = ["friendly", "bold"]
        voice.mark_distilled()
        voice.save()
        block = generation.PromptEnhancer.voice_block(voice)
        self.assertIn("warm and direct", block)
        self.assertIn("friendly", block)

    def test_voice_block_empty_when_not_distilled(self):
        voice = VoiceProfile.get_solo()  # not distilled
        self.assertEqual(generation.PromptEnhancer.voice_block(voice), "")


class DistillVoiceTests(TestCase):
    @patch("content_calendar.generation.ai_client.generate")
    def test_distill_saves_singleton(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "summary": "punchy and warm",
            "tone_words": ["bold", "warm"],
            "sentence_length": "short",
            "words_to_avoid": ["synergy"],
            "sample_paragraphs": ["Hello there."],
            "do_notes": ["be direct"],
            "dont_notes": ["don't ramble"],
        })
        voice = generation.distill_voice("some writing samples")
        self.assertEqual(voice.pk, 1)
        self.assertEqual(voice.summary, "punchy and warm")
        self.assertEqual(voice.sentence_length, "short")
        self.assertTrue(voice.is_distilled)
        self.assertEqual(VoiceProfile.objects.count(), 1)

    @patch("content_calendar.generation.ai_client.generate")
    def test_distill_defaults_bad_sentence_length(self, mock_generate):
        mock_generate.return_value = json.dumps({"sentence_length": "epic"})
        voice = generation.distill_voice("x")
        self.assertEqual(voice.sentence_length, "varied")


class GenerationTests(TestCase):
    @patch("content_calendar.generation.ai_client.generate")
    def test_generate_from_brief_creates_ready_draft(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "topic": "Summer skincare",
            "hook": "Melting in the heat?",
            "caption": "Here's how to keep skin fresh.",
            "call_to_action": "Save this post.",
            "hashtags": "#skincare #summer",
        })
        item = generation.generate_content_item(brief="summer skincare", content_type="social")
        self.assertEqual(item.approval_status, "ready")
        self.assertEqual(item.status, "draft")
        self.assertEqual(item.topic, "Summer skincare")
        self.assertEqual(item.hook, "Melting in the heat?")

    @patch("content_calendar.generation.ai_client.generate")
    def test_generate_from_template_runs_prompts_in_order(self, mock_generate):
        mock_generate.side_effect = ["A hook", "A caption", "A CTA"]
        template = ContentTemplate.objects.create(name="IG Post", content_type="reel")
        ContentTemplatePrompt.objects.create(template=template, name="Hook", target_field="hook", prompt="hook", order=1)
        ContentTemplatePrompt.objects.create(template=template, name="Caption", target_field="caption", prompt="caption", order=2)
        ContentTemplatePrompt.objects.create(template=template, name="CTA", target_field="call_to_action", prompt="cta", order=3)

        item = generation.generate_content_item(template=template, brief="a brief")
        self.assertEqual(item.hook, "A hook")
        self.assertEqual(item.caption, "A caption")
        self.assertEqual(item.call_to_action, "A CTA")
        self.assertEqual(item.content_type, "reel")
        self.assertEqual(mock_generate.call_count, 3)


class GenerateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="tester", password="pw12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_generate_requires_template_or_brief(self):
        resp = self.client.post(reverse("content_calendar:generate"), data={"brief": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Choose a template or write a brief")

    @patch("content_calendar.generation.ai_client.generate")
    def test_generate_creates_item_and_redirects(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "topic": "T", "hook": "H", "caption": "C",
            "call_to_action": "CTA", "hashtags": "#h",
        })
        resp = self.client.post(reverse("content_calendar:generate"),
                                data={"brief": "make something", "content_type": "reel"})
        self.assertEqual(resp.status_code, 302)
        item = ContentItem.objects.latest("created_at")
        self.assertEqual(item.approval_status, "ready")
        self.assertIn(f"/content/{item.pk}/edit/", resp.url)

    def test_generate_reports_missing_provider(self):
        # No active AIProviderConfig → AIConfigError surfaced on the form.
        resp = self.client.post(reverse("content_calendar:generate"),
                                data={"brief": "make something"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No active AI provider")
