# pages/context_processors.py
from .models import Page


def sidebar(request):
    """Root pages and favorites for the left sidebar (authenticated users only)."""
    if not request.user.is_authenticated:
        return {}
    return {
        "sidebar_root_pages": Page.objects.filter(
            parent__isnull=True, is_archived=False
        ),
        "sidebar_favorites": Page.objects.filter(is_favorite=True, is_archived=False),
    }
