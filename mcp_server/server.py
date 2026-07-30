# mcp_server/server.py
"""MCP server exposing the content-calendar tools over stdio.

This is a second transport for the exact same tool functions the chat assistant
uses (ai_assistant.tools) — no new business logic. Point Claude Desktop / Cowork
/ Claude Code at it (see mcp_server/README.md) to manage the calendar directly.

Run it with:  python manage.py runmcp   (stdio transport)
"""
import os

import django
from django.apps import apps

# FastMCP invokes sync tools inside its asyncio loop, which trips Django's
# "cannot call this from an async context" ORM guard. This is a single-user,
# local stdio server that handles one request at a time, so briefly running a
# SQLite query on the loop thread is safe — opt out of the guard rather than
# thread every ORM call. Must be set before any ORM use.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

# Works both as a standalone script (`python -m mcp_server.server`) and when
# imported after Django is already configured (the runmcp management command).
if not apps.ready:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

from mcp.server.fastmcp import FastMCP

from ai_assistant import tools

INSTRUCTIONS = (
    "Manage a personal content calendar: list, create, schedule, review and "
    "generate social content. Dates are ISO strings (YYYY-MM-DD)."
)

mcp = FastMCP("content-calendar", instructions=INSTRUCTIONS)


@mcp.tool()
def create_content_item(
    topic: str,
    scheduled_date: str = "",
    content_type: str = "",
    pillar: str = "",
    hook: str = "",
    caption: str = "",
    call_to_action: str = "",
    hashtags: str = "",
    status: str = "idea",
    approval_status: str = "draft",
    project_id: int | None = None,
    platforms: list[str] | None = None,
) -> dict:
    """Create a new content item. `topic` is required; dates are YYYY-MM-DD.
    content_type is one of reel/carousel/single_image/story/video/live/text;
    status is idea/draft/scheduled/published/archived; approval_status is
    draft/ready/approved/changes."""
    return tools.create_content_item(
        topic=topic, scheduled_date=scheduled_date or None, content_type=content_type,
        pillar=pillar, hook=hook, caption=caption, call_to_action=call_to_action,
        hashtags=hashtags, status=status, approval_status=approval_status,
        project_id=project_id, platforms=platforms,
    )


@mcp.tool()
def list_content_items(
    start_date: str = "",
    end_date: str = "",
    status: str = "",
    approval_status: str = "",
) -> dict:
    """List content items, optionally filtered by scheduled-date range and/or
    status/approval_status. Dates are YYYY-MM-DD."""
    return tools.list_content_items(
        start_date=start_date or None, end_date=end_date or None,
        status=status or None, approval_status=approval_status or None,
    )


@mcp.tool()
def update_status(item_id: int, status: str) -> dict:
    """Set a content item's status. Accepts a pipeline status
    (idea/draft/scheduled/published/archived) or an approval status
    (draft/ready/approved/changes)."""
    return tools.update_status(item_id, status)


@mcp.tool()
def reschedule_content_item(item_id: int, scheduled_date: str = "") -> dict:
    """Move a content item to a different date (YYYY-MM-DD), or clear it when
    scheduled_date is empty."""
    return tools.reschedule_content_item(item_id, scheduled_date or None)


@mcp.tool()
def generate_draft(brief: str = "", template_id: int | None = None, date: str = "") -> dict:
    """Generate a draft content item from a brief and/or a content template,
    using the active AI provider. Returns the created item (approval 'ready')."""
    return tools.generate_draft(brief=brief, template_id=template_id, date=date or None)


@mcp.tool()
def distill_voice(samples: str) -> dict:
    """Distil writing samples into the reusable voice profile used by the
    generator."""
    return tools.distill_voice(samples)


@mcp.tool()
def get_calendar_month(year: int, month: int) -> dict:
    """List all content scheduled in a given month (month is 1-12)."""
    return tools.get_calendar_month(year, month)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
