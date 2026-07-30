# content_calendar/tests.py
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import ContentItem, Platform


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
