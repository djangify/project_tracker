# ai_assistant/tests.py
import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ai_settings.ai_client import ToolCall, ToolTurn
from content_calendar.models import ContentItem

from . import agent, tools


class ToolFunctionTests(TestCase):
    def test_create_and_list(self):
        result = tools.create_content_item(topic="Hello world", scheduled_date="2026-08-10",
                                           content_type="reel")
        self.assertIn("id", result)
        self.assertEqual(result["topic"], "Hello world")

        listed = tools.list_content_items(start_date="2026-08-01", end_date="2026-08-31")
        self.assertEqual(listed["count"], 1)

    def test_create_requires_topic(self):
        out = tools.execute_tool("create_content_item", {"topic": ""})
        self.assertIn("error", out)

    def test_update_status_pipeline_and_approval(self):
        item = ContentItem.objects.create(topic="X")
        tools.update_status(item.id, "scheduled")
        item.refresh_from_db()
        self.assertEqual(item.status, "scheduled")
        tools.update_status(item.id, "approved")
        item.refresh_from_db()
        self.assertEqual(item.approval_status, "approved")

    def test_update_status_invalid(self):
        item = ContentItem.objects.create(topic="X")
        out = tools.execute_tool("update_status", {"item_id": item.id, "status": "nope"})
        self.assertIn("error", out)

    def test_reschedule(self):
        item = ContentItem.objects.create(topic="X", scheduled_date=date(2026, 8, 1))
        tools.reschedule_content_item(item.id, "2026-08-20")
        item.refresh_from_db()
        self.assertEqual(item.scheduled_date, date(2026, 8, 20))

    def test_bad_date_reported(self):
        out = tools.execute_tool("reschedule_content_item", {"item_id": 1, "scheduled_date": "not-a-date"})
        self.assertIn("error", out)

    def test_get_calendar_month(self):
        ContentItem.objects.create(topic="Aug", scheduled_date=date(2026, 8, 15))
        ContentItem.objects.create(topic="Sep", scheduled_date=date(2026, 9, 1))
        out = tools.get_calendar_month(2026, 8)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["items"][0]["topic"], "Aug")

    @patch("content_calendar.generation.ai_client.generate")
    def test_generate_draft(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "topic": "Drafted", "hook": "H", "caption": "C",
            "call_to_action": "CTA", "hashtags": "#x",
        })
        out = tools.generate_draft(brief="something", date="2026-08-05")
        self.assertEqual(out["topic"], "Drafted")
        self.assertEqual(out["approval_status"], "ready")

    def test_unknown_tool(self):
        self.assertIn("error", tools.execute_tool("does_not_exist", {}))

    def test_schemas_cover_all_tools(self):
        names = {s["name"] for s in tools.tool_schemas()}
        self.assertEqual(names, set(tools.TOOLS.keys()))


class AgentLoopTests(TestCase):
    @patch("ai_assistant.agent.ai_client.generate_with_tools")
    def test_loop_executes_tool_then_replies(self, mock_gwt):
        # First call asks to create an item; second call replies in text.
        mock_gwt.side_effect = [
            ToolTurn(text=None, tool_calls=[
                ToolCall(id="c1", name="create_content_item",
                         arguments={"topic": "Made by tool", "scheduled_date": "2026-08-09"})
            ]),
            ToolTurn(text="Done — created your post.", tool_calls=[]),
        ]
        reply, messages = agent.run_turn([{"role": "user", "content": "make a post"}])
        self.assertEqual(reply, "Done — created your post.")
        self.assertTrue(ContentItem.objects.filter(topic="Made by tool").exists())
        # Conversation contains a tool result message.
        self.assertTrue(any(m["role"] == "tool" for m in messages))

    @patch("ai_assistant.agent.ai_client.generate_with_tools")
    def test_loop_stops_at_max_steps(self, mock_gwt):
        # Always returns a tool call → loop must give up after MAX_STEPS.
        mock_gwt.return_value = ToolTurn(
            text=None,
            tool_calls=[ToolCall(id="c", name="list_content_items", arguments={})],
        )
        reply, _ = agent.run_turn([{"role": "user", "content": "loop forever"}])
        self.assertIn("stopped", reply.lower())
        self.assertEqual(mock_gwt.call_count, agent.MAX_STEPS)

    def test_display_messages_filters_tool_traffic(self):
        convo = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "1", "name": "x", "arguments": {}}]},
            {"role": "tool", "tool_call_id": "1", "name": "x", "content": "{}"},
            {"role": "assistant", "content": "hello!"},
        ]
        shown = agent.display_messages(convo)
        self.assertEqual(shown, [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello!"},
        ])


class ChatViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="tester", password="pw12345")

    def setUp(self):
        self.client.force_login(self.user)

    def test_chat_page_renders(self):
        resp = self.client.get(reverse("ai_assistant:chat"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Assistant")

    @patch("ai_assistant.agent.ai_client.generate_with_tools")
    def test_send_appends_and_returns_transcript(self, mock_gwt):
        mock_gwt.return_value = ToolTurn(text="Hi there!", tool_calls=[])
        resp = self.client.post(reverse("ai_assistant:send"), data={"message": "hello"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "hello")
        self.assertContains(resp, "Hi there!")

    def test_send_without_provider_shows_error(self):
        resp = self.client.post(reverse("ai_assistant:send"), data={"message": "hello"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No active AI provider")

    def test_clear_resets_session(self):
        self.client.post(reverse("ai_assistant:send"), data={"message": "hello"})
        resp = self.client.post(reverse("ai_assistant:clear"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.client.session.get("assistant_messages"), [])

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("ai_assistant:chat"))
        self.assertEqual(resp.status_code, 302)
