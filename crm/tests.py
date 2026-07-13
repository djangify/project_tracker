# crm/tests.py
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from .models import Contact


class ContactProjectLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pw")
        self.client.login(username="tester", password="pw")
        self.project = Project.objects.create(name="Djangify")

    def test_contact_links_to_project(self):
        c = Contact.objects.create(name="Sam", project=self.project)
        self.assertEqual(list(self.project.contacts.all()), [c])

    def test_deleting_project_keeps_contact(self):
        c = Contact.objects.create(name="Sam", project=self.project)
        self.project.delete()
        c.refresh_from_db()
        self.assertIsNone(c.project)  # SET_NULL

    def test_joined_email_list_field(self):
        c = Contact.objects.create(name="Ada", joined_email_list=True)
        self.assertTrue(c.joined_email_list)
        # old name is gone
        self.assertFalse(hasattr(c, "joined_live_it_list"))

    def test_create_form_accepts_project(self):
        self.client.post(
            reverse("crm:contact_create"),
            {
                "name": "Jo",
                "platform": "instagram",
                "status": "new",
                "project": self.project.id,
                "joined_email_list": "on",
            },
        )
        jo = Contact.objects.get(name="Jo")
        self.assertEqual(jo.project, self.project)
        self.assertTrue(jo.joined_email_list)

    def test_project_detail_lists_contacts(self):
        Contact.objects.create(name="Visible Person", project=self.project)
        resp = self.client.get(
            reverse("projects:project_detail", args=[self.project.id])
        )
        self.assertContains(resp, "Visible Person")
        self.assertContains(resp, "People I've spoken to")
