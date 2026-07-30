# mcp_server/tests.py
import asyncio

from django.test import TestCase

from content_calendar.models import ContentItem

from . import server


class McpServerTests(TestCase):
    def test_all_tools_registered(self):
        listed = asyncio.run(server.mcp.list_tools())
        names = {t.name for t in listed}
        self.assertEqual(names, {
            "create_content_item", "list_content_items", "update_status",
            "reschedule_content_item", "generate_draft", "distill_voice",
            "get_calendar_month",
        })

    def test_create_content_item_required_topic_in_schema(self):
        listed = asyncio.run(server.mcp.list_tools())
        create = next(t for t in listed if t.name == "create_content_item")
        self.assertEqual(create.inputSchema.get("required"), ["topic"])

    def test_wrapper_create_and_list(self):
        # @mcp.tool() returns the original function, so the wrappers are
        # directly callable and exercise the same tools + ORM the assistant uses.
        out = server.create_content_item(topic="Via MCP", scheduled_date="2026-08-12")
        self.assertEqual(out["topic"], "Via MCP")
        self.assertEqual(out["scheduled_date"], "2026-08-12")

        listed = server.list_content_items(start_date="2026-08-01", end_date="2026-08-31")
        self.assertEqual(listed["count"], 1)

    def test_wrapper_update_status(self):
        item = ContentItem.objects.create(topic="X")
        server.update_status(item.id, "published")
        item.refresh_from_db()
        self.assertEqual(item.status, "published")

    def test_wrapper_get_calendar_month(self):
        from datetime import date
        ContentItem.objects.create(topic="Aug", scheduled_date=date(2026, 8, 3))
        out = server.get_calendar_month(2026, 8)
        self.assertEqual(out["count"], 1)
