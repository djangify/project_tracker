# ai_assistant/management/commands/connect_claude.py
import sys
from pathlib import Path

from django.core.management.base import BaseCommand

from mcp_server.desktop_connect import claude_config_path, connect


class Command(BaseCommand):
    help = "Register this install with Claude Desktop (adds the content-calendar MCP server)."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]
        frozen = getattr(sys, "frozen", False)
        status = connect(base_dir, frozen)

        cfg = claude_config_path()
        if status in ("connected", "updated", "unchanged"):
            self.stdout.write(self.style.SUCCESS(
                f"Claude Desktop: {status} ({cfg})."
            ))
            self.stdout.write("Fully quit and reopen Claude Desktop to load the change.")
        elif status == "no-claude":
            self.stdout.write(self.style.WARNING(
                "Claude Desktop not found — nothing changed. Install Claude Desktop, then run this again."
            ))
        else:
            self.stderr.write(self.style.ERROR(f"Could not connect: {status}"))
