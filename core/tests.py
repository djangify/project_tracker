# core/tests.py
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from projects.models import Project, Task


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pw")
        self.today = timezone.localdate()

    def test_login_required(self):
        resp = self.client.get(reverse("core:home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_dashboard_renders_panels(self):
        self.client.login(username="tester", password="pw")
        resp = self.client.get(reverse("core:home"))
        self.assertEqual(resp.status_code, 200)
        for label in ["Dashboard", "Today", "My Week", "All Tasks", "Work Log"]:
            self.assertContains(resp, label)

    def test_today_panel_lists_scheduled_and_overdue(self):
        p = Project.objects.create(name="Djangify")
        Task.objects.create(project=p, title="Due today", scheduled_date=self.today)
        yesterday = self.today - timezone.timedelta(days=1)
        Task.objects.create(project=p, title="Was due", scheduled_date=yesterday)
        done = Task.objects.create(
            project=p, title="Already done", scheduled_date=self.today, status="done"
        )

        self.client.login(username="tester", password="pw")
        resp = self.client.get(reverse("core:home"))
        today_titles = [t.title for t in resp.context["today_tasks"]]
        overdue_titles = [t.title for t in resp.context["overdue_tasks"]]
        self.assertIn("Due today", today_titles)
        self.assertIn("Was due", overdue_titles)
        # done tasks are excluded from the open Today/Overdue lists
        self.assertNotIn("Already done", today_titles)
        self.assertNotIn("Already done", overdue_titles)

    def test_week_clash_badge_when_two_projects_share_a_day(self):
        p1 = Project.objects.create(name="Djangify")
        p2 = Project.objects.create(name="Inspirational Guidance")
        Task.objects.create(project=p1, title="A", scheduled_date=self.today)
        Task.objects.create(project=p2, title="B", scheduled_date=self.today)

        self.client.login(username="tester", password="pw")
        resp = self.client.get(reverse("core:home"))
        self.assertContains(resp, "businesses")  # "⚠ 2 businesses" clash badge

    def test_no_clash_badge_for_single_project_day(self):
        p1 = Project.objects.create(name="Djangify")
        Task.objects.create(project=p1, title="A", scheduled_date=self.today)
        Task.objects.create(project=p1, title="B", scheduled_date=self.today)

        self.client.login(username="tester", password="pw")
        resp = self.client.get(reverse("core:home"))
        self.assertNotContains(resp, "businesses")
