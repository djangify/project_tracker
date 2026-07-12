# projects/tests.py
import datetime

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
