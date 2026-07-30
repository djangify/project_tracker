# ai_assistant/tools.py
"""The assistant's tool set — plain Python functions over the content calendar
and generation engine.

These are the single source of truth for what the assistant (Phase 4) and the
MCP server (Phase 5) can do. Each function takes JSON-friendly arguments and
returns a JSON-serializable dict, so the same functions work behind a provider's
tool-calling API and behind MCP's @server.tool() decorators.
"""
from datetime import date

from content_calendar import generation
from content_calendar.models import ContentItem, ContentTemplate
from projects.models import Project

MAX_LIST = 100


class ToolError(Exception):
    """A tool failed in a way worth reporting back to the model/user."""


def _parse_date(value, field="date"):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ToolError(f"{field} must be YYYY-MM-DD, got {value!r}")


def _item_dict(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "topic": item.topic,
        "scheduled_date": item.scheduled_date.isoformat() if item.scheduled_date else None,
        "content_type": item.content_type,
        "pillar": item.pillar,
        "hook": item.hook,
        "caption": item.caption,
        "call_to_action": item.call_to_action,
        "hashtags": item.hashtags,
        "status": item.status,
        "approval_status": item.approval_status,
        "platforms": [p.name for p in item.platforms.all()],
        "project": item.project.name if item.project else None,
    }


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------
def create_content_item(topic, scheduled_date=None, content_type="", pillar="",
                        hook="", caption="", call_to_action="", hashtags="",
                        status="idea", approval_status="draft", project_id=None,
                        platforms=None):
    """Create a content item with the given fields."""
    if not topic:
        raise ToolError("topic is required")
    project = None
    if project_id:
        project = Project.objects.filter(pk=project_id).first()
        if project is None:
            raise ToolError(f"No project with id {project_id}")

    if status not in dict(ContentItem.STATUS_CHOICES):
        status = "idea"
    if approval_status not in dict(ContentItem.APPROVAL_STATUS_CHOICES):
        approval_status = "draft"

    item = ContentItem.objects.create(
        topic=topic,
        scheduled_date=_parse_date(scheduled_date, "scheduled_date"),
        content_type=content_type or "",
        pillar=pillar or "",
        hook=hook or "",
        caption=caption or "",
        call_to_action=call_to_action or "",
        hashtags=hashtags or "",
        status=status,
        approval_status=approval_status,
        project=project,
    )
    if platforms:
        from content_calendar.models import Platform
        item.platforms.set(Platform.objects.filter(name__in=platforms))
    return _item_dict(item)


def list_content_items(start_date=None, end_date=None, status=None, approval_status=None):
    """List content items, optionally filtered by scheduled-date range/status."""
    qs = ContentItem.objects.select_related("project").prefetch_related("platforms")
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")
    if start:
        qs = qs.filter(scheduled_date__gte=start)
    if end:
        qs = qs.filter(scheduled_date__lte=end)
    if status:
        qs = qs.filter(status=status)
    if approval_status:
        qs = qs.filter(approval_status=approval_status)
    qs = qs.order_by("scheduled_date", "order")[:MAX_LIST]
    return {"count": len(qs), "items": [_item_dict(i) for i in qs]}


def update_status(item_id, status):
    """Set a content item's status. Accepts either a pipeline status
    (idea/draft/scheduled/published/archived) or an approval status
    (draft/ready/approved/changes)."""
    item = ContentItem.objects.filter(pk=item_id).first()
    if item is None:
        raise ToolError(f"No content item with id {item_id}")
    if status in dict(ContentItem.STATUS_CHOICES):
        item.status = status
    elif status in dict(ContentItem.APPROVAL_STATUS_CHOICES):
        item.approval_status = status
    else:
        raise ToolError(f"Unknown status {status!r}")
    item.save()
    return _item_dict(item)


def reschedule_content_item(item_id, scheduled_date):
    """Move a content item to a different date (YYYY-MM-DD), or clear it (null)."""
    item = ContentItem.objects.filter(pk=item_id).first()
    if item is None:
        raise ToolError(f"No content item with id {item_id}")
    item.scheduled_date = _parse_date(scheduled_date, "scheduled_date")
    item.save()
    return _item_dict(item)


def generate_draft(brief="", template_id=None, date=None):
    """Generate a draft content item from a brief and/or a template, using the
    active AI provider. Returns the created item."""
    template = None
    if template_id:
        template = ContentTemplate.objects.filter(pk=template_id).first()
        if template is None:
            raise ToolError(f"No template with id {template_id}")
    if not template and not (brief or "").strip():
        raise ToolError("Provide a brief or a template_id")
    item = generation.generate_content_item(
        template=template,
        brief=(brief or "").strip(),
        scheduled_date=_parse_date(date, "date"),
    )
    return _item_dict(item)


def distill_voice(samples):
    """Distil writing samples into the reusable voice profile."""
    if not (samples or "").strip():
        raise ToolError("samples text is required")
    voice = generation.distill_voice(samples)
    return {
        "name": voice.name,
        "summary": voice.summary,
        "tone_words": voice.tone_words,
        "sentence_length": voice.sentence_length,
        "words_to_avoid": voice.words_to_avoid,
        "is_active": voice.is_active,
    }


def get_calendar_month(year, month):
    """List all content scheduled in a given month."""
    try:
        first = date(int(year), int(month), 1)
    except (ValueError, TypeError):
        raise ToolError("year and month must be valid numbers")
    if month == 12:
        end = date(int(year), 12, 31)
    else:
        from datetime import timedelta
        end = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    return list_content_items(start_date=first.isoformat(), end_date=end.isoformat())


# ---------------------------------------------------------------------------
# Registry: schema (for provider tool-calling) + dispatch
# ---------------------------------------------------------------------------
def _schema(properties, required=None):
    return {"type": "object", "properties": properties, "required": required or []}


TOOLS = {
    "create_content_item": {
        "fn": create_content_item,
        "description": "Create a new content item in the calendar.",
        "parameters": _schema({
            "topic": {"type": "string", "description": "Short topic/title"},
            "scheduled_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
            "content_type": {"type": "string", "description": "reel, carousel, single_image, story, video, live or text"},
            "pillar": {"type": "string"},
            "hook": {"type": "string"},
            "caption": {"type": "string"},
            "call_to_action": {"type": "string"},
            "hashtags": {"type": "string"},
            "status": {"type": "string", "description": "idea, draft, scheduled, published or archived"},
            "approval_status": {"type": "string", "description": "draft, ready, approved or changes"},
            "project_id": {"type": "integer"},
            "platforms": {"type": "array", "items": {"type": "string"}, "description": "Platform names"},
        }, required=["topic"]),
    },
    "list_content_items": {
        "fn": list_content_items,
        "description": "List content items, optionally filtered by date range and status.",
        "parameters": _schema({
            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            "status": {"type": "string"},
            "approval_status": {"type": "string"},
        }),
    },
    "update_status": {
        "fn": update_status,
        "description": "Set a content item's pipeline status or approval status.",
        "parameters": _schema({
            "item_id": {"type": "integer"},
            "status": {"type": "string", "description": "A pipeline status or an approval status"},
        }, required=["item_id", "status"]),
    },
    "reschedule_content_item": {
        "fn": reschedule_content_item,
        "description": "Move a content item to a different scheduled date.",
        "parameters": _schema({
            "item_id": {"type": "integer"},
            "scheduled_date": {"type": "string", "description": "YYYY-MM-DD, or null to unschedule"},
        }, required=["item_id"]),
    },
    "generate_draft": {
        "fn": generate_draft,
        "description": "Generate a draft content item from a brief and/or a template.",
        "parameters": _schema({
            "brief": {"type": "string"},
            "template_id": {"type": "integer"},
            "date": {"type": "string", "description": "YYYY-MM-DD, optional"},
        }),
    },
    "distill_voice": {
        "fn": distill_voice,
        "description": "Distil writing samples into the reusable voice profile.",
        "parameters": _schema({
            "samples": {"type": "string", "description": "Writing samples to analyse"},
        }, required=["samples"]),
    },
    "get_calendar_month": {
        "fn": get_calendar_month,
        "description": "List all content scheduled in a given month.",
        "parameters": _schema({
            "year": {"type": "integer"},
            "month": {"type": "integer", "description": "1-12"},
        }, required=["year", "month"]),
    },
}


def tool_schemas() -> list[dict]:
    """The tool definitions in the adapter's normalized shape."""
    return [
        {"name": name, "description": spec["description"], "parameters": spec["parameters"]}
        for name, spec in TOOLS.items()
    ]


def execute_tool(name: str, arguments: dict) -> dict:
    """Run a tool by name. Always returns a dict (errors wrapped as {'error': ...})."""
    spec = TOOLS.get(name)
    if spec is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return spec["fn"](**(arguments or {}))
    except ToolError as exc:
        return {"error": str(exc)}
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
    except Exception as exc:  # noqa: BLE001 — report to the model rather than crash the loop
        return {"error": f"{type(exc).__name__}: {exc}"}
