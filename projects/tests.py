# projects/tests.py
import datetime
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Project, Task, WorkSession


class TaskStatusTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Djangify")

    def test_status_drives_is_completed(self):
        task = Task.objects.create(project=self.project, title="A", status="done")
        self.assertTrue(task.is_completed)

        task.status = "in_progress"
        task.save()
        self.assertFalse(task.is_completed)

    def test_default_status_is_planned(self):
        task = Task.objects.create(project=self.project, title="B")
        self.assertEqual(task.status, "planned")
        self.assertFalse(task.is_completed)

    def test_is_overdue(self):
        yesterday = timezone.localdate() - datetime.timedelta(days=1)
        overdue = Task.objects.create(
            project=self.project, title="late", scheduled_date=yesterday
        )
        self.assertTrue(overdue.is_overdue)

        done = Task.objects.create(
            project=self.project, title="late but done",
            scheduled_date=yesterday, status="done",
        )
        self.assertFalse(done.is_overdue)

        unscheduled = Task.objects.create(project=self.project, title="someday")
        self.assertFalse(unscheduled.is_overdue)


class WorkSessionLinkTests(TestCase):
    def test_session_links_to_task(self):
        project = Project.objects.create(name="Inspirational Guidance")
        task = Task.objects.create(project=project, title="Write post")
        session = WorkSession.objects.create(
            project=project, task=task, start_time=timezone.now()
        )
        self.assertEqual(list(task.work_sessions.all()), [session])

    def test_deleting_task_keeps_session(self):
        project = Project.objects.create(name="P")
        task = Task.objects.create(project=project, title="T")
        session = WorkSession.objects.create(
            project=project, task=task, start_time=timezone.now()
        )
        task.delete()
        session.refresh_from_db()
        self.assertIsNone(session.task)  # SET_NULL


class TaskViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pw")
        self.client.login(username="tester", password="pw")
        self.project = Project.objects.create(name="Djangify")

    def test_toggle_flips_status(self):
        task = Task.objects.create(project=self.project, title="Toggle me")
        self.client.post(reverse("projects:task_toggle", args=[task.id]))
        task.refresh_from_db()
        self.assertEqual(task.status, "done")
        self.assertTrue(task.is_completed)

        self.client.post(reverse("projects:task_toggle", args=[task.id]))
        task.refresh_from_db()
        self.assertEqual(task.status, "planned")
        self.assertFalse(task.is_completed)

    def test_create_task_with_scheduled_date(self):
        self.client.post(
            reverse("projects:task_create", args=[self.project.id]),
            {"title": "Dated task", "description": "", "scheduled_date": "2026-07-20"},
        )
        task = Task.objects.get(title="Dated task")
        self.assertEqual(task.scheduled_date, datetime.date(2026, 7, 20))
        self.assertEqual(task.status, "planned")


class TaskViewsTests(TestCase):
    """Phase C: Table / Board / Calendar + set-status + quick create."""

    def setUp(self):
        self.user = User.objects.create_user("tester", password="pw")
        self.client.login(username="tester", password="pw")
        self.p1 = Project.objects.create(name="Djangify")
        self.p2 = Project.objects.create(name="Inspirational Guidance")

    def test_table_renders_and_filters_by_project(self):
        Task.objects.create(project=self.p1, title="Djangify task")
        Task.objects.create(project=self.p2, title="IG task")
        resp = self.client.get(reverse("projects:task_table"))
        self.assertContains(resp, "Djangify task")
        self.assertContains(resp, "IG task")
        # filtered
        resp = self.client.get(reverse("projects:task_table") + f"?project={self.p1.id}")
        self.assertContains(resp, "Djangify task")
        self.assertNotContains(resp, "IG task")

    def test_board_groups_by_status(self):
        Task.objects.create(project=self.p1, title="Planned one", status="planned")
        Task.objects.create(project=self.p1, title="Doing one", status="in_progress")
        Task.objects.create(project=self.p1, title="Done one", status="done")
        resp = self.client.get(reverse("projects:task_board"))
        cols = {c["key"]: c for c in resp.context["columns"]}
        self.assertEqual([t.title for t in cols["planned"]["tasks"]], ["Planned one"])
        self.assertEqual([t.title for t in cols["in_progress"]["tasks"]], ["Doing one"])
        self.assertEqual([t.title for t in cols["done"]["tasks"]], ["Done one"])

    def test_set_status_endpoint(self):
        task = Task.objects.create(project=self.p1, title="Move me")
        resp = self.client.post(
            reverse("projects:task_set_status", args=[task.id]),
            data=json.dumps({"status": "in_progress"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")

    def test_set_status_rejects_invalid(self):
        task = Task.objects.create(project=self.p1, title="X")
        resp = self.client.post(
            reverse("projects:task_set_status", args=[task.id]),
            data=json.dumps({"status": "bogus"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        task.refresh_from_db()
        self.assertEqual(task.status, "planned")

    def test_calendar_renders(self):
        today = timezone.localdate()
        Task.objects.create(project=self.p1, title="Cal task", scheduled_date=today)
        resp = self.client.get(reverse("projects:task_calendar"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cal task")

    def test_quick_create(self):
        self.client.post(
            reverse("projects:task_quick_create"),
            {"project": self.p1.id, "title": "Quick", "status": "planned",
             "scheduled_date": "2026-07-20", "estimate_minutes": "30"},
        )
        task = Task.objects.get(title="Quick")
        self.assertEqual(task.project, self.p1)
        self.assertEqual(task.estimate_minutes, 30)
