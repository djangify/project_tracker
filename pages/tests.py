# pages/tests.py
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Page


class PageModelTests(TestCase):
    def test_str_and_ancestors(self):
        root = Page.objects.create(title="Root", icon="📁")
        child = Page.objects.create(title="Child", parent=root)
        grandchild = Page.objects.create(title="Grandchild", parent=child)

        self.assertEqual(str(root), "📁 Root")
        self.assertEqual(grandchild.ancestors(), [root, child])
        self.assertEqual(list(root.visible_children()), [child])

    def test_visible_children_excludes_archived(self):
        root = Page.objects.create(title="Root")
        keep = Page.objects.create(title="Keep", parent=root)
        Page.objects.create(title="Gone", parent=root, is_archived=True)
        self.assertEqual(list(root.visible_children()), [keep])


class PageViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pw")
        self.client.login(username="tester", password="pw")

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("pages:trash"))
        self.assertEqual(resp.status_code, 302)

    def test_create_redirects_to_new_page(self):
        resp = self.client.post(reverse("pages:create"))
        page = Page.objects.get()
        self.assertRedirects(resp, page.get_absolute_url())
        self.assertEqual(page.title, "Untitled")

    def test_create_subpage_with_parent(self):
        root = Page.objects.create(title="Root")
        self.client.post(reverse("pages:create") + f"?parent={root.id}")
        child = Page.objects.exclude(pk=root.pk).get()
        self.assertEqual(child.parent, root)

    def test_detail_renders(self):
        page = Page.objects.create(title="Hello")
        resp = self.client.get(page.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Hello")

    def test_content_autosave(self):
        page = Page.objects.create(title="Old")
        payload = {"title": "New title", "icon": "🚀", "content": {"blocks": [1]}}
        resp = self.client.post(
            reverse("pages:content", args=[page.id]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "New title")
        self.assertEqual(page.icon, "🚀")
        self.assertEqual(page.content, {"blocks": [1]})

    def test_blank_title_falls_back_to_untitled(self):
        page = Page.objects.create(title="Something")
        self.client.post(
            reverse("pages:content", args=[page.id]),
            data=json.dumps({"title": "   "}),
            content_type="application/json",
        )
        page.refresh_from_db()
        self.assertEqual(page.title, "Untitled")

    def test_favorite_toggle(self):
        page = Page.objects.create(title="Fav")
        resp = self.client.post(reverse("pages:favorite", args=[page.id]))
        self.assertJSONEqual(resp.content, {"is_favorite": True})
        page.refresh_from_db()
        self.assertTrue(page.is_favorite)

    def test_archive_and_restore(self):
        page = Page.objects.create(title="Temp")
        self.client.post(reverse("pages:archive", args=[page.id]))
        page.refresh_from_db()
        self.assertTrue(page.is_archived)

        self.client.post(reverse("pages:restore", args=[page.id]))
        page.refresh_from_db()
        self.assertFalse(page.is_archived)

    def test_hard_delete_from_trash(self):
        page = Page.objects.create(title="Doomed", is_archived=True)
        self.client.post(reverse("pages:delete", args=[page.id]))
        self.assertFalse(Page.objects.filter(pk=page.pk).exists())
