# mcp_server/tests.py
import asyncio
import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase, TestCase

from content_calendar.models import ContentItem

from . import desktop_connect, server


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


class DesktopConnectTests(SimpleTestCase):
    """The Claude Desktop auto-connect config merge. No DB needed."""

    def _cfg(self, tmp):
        d = Path(tmp) / "Claude"
        d.mkdir()
        return d / "claude_desktop_config.json"

    def test_connects_when_config_dir_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            status = desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            self.assertEqual(status, "connected")
            data = json.loads(cfg.read_text())
            self.assertIn("content-calendar", data["mcpServers"])

    def test_idempotent_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            status = desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            self.assertEqual(status, "unchanged")

    def test_preserves_other_keys_and_servers(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            cfg.write_text(json.dumps({
                "coworkUserFilesPath": "C:/x",
                "mcpServers": {"other": {"command": "x"}},
            }))
            desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            data = json.loads(cfg.read_text())
            self.assertEqual(data["coworkUserFilesPath"], "C:/x")
            self.assertIn("other", data["mcpServers"])
            self.assertIn("content-calendar", data["mcpServers"])

    def test_no_claude_when_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "Claude" / "claude_desktop_config.json"  # dir not created
            status = desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            self.assertEqual(status, "no-claude")

    def test_refuses_to_clobber_unreadable_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = self._cfg(tmp)
            cfg.write_text("{ this is not json ]")
            status = desktop_connect.connect(Path("/proj"), frozen=False, config_path=cfg)
            self.assertTrue(status.startswith("error"))
            # Original content left untouched.
            self.assertEqual(cfg.read_text(), "{ this is not json ]")

    def test_dev_entry_uses_manage_py(self):
        entry = desktop_connect.server_entry(Path("/proj"), frozen=False)
        self.assertEqual(entry["args"], ["manage.py", "runmcp"])
        self.assertEqual(entry["cwd"], str(Path("/proj")))

    def test_frozen_entry_points_at_mcp_exe(self):
        entry = desktop_connect.server_entry(Path("/proj"), frozen=True)
        self.assertTrue(entry["command"].endswith("ProjectTracker-mcp.exe")
                        or entry["command"].endswith("ProjectTracker-mcp"))
        self.assertEqual(entry["args"], [])
