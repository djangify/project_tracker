"""Console entry point for the content-calendar MCP server (stdio).

Used two ways:
  - Packaged: PyInstaller builds this as ProjectTracker-mcp.exe (a *console*
    executable — a windowed .exe has no stdin/stdout, which stdio MCP needs).
    Claude Desktop launches it. See project_tracker.spec.
  - Dev:      python mcp_launcher.py   (equivalent to `python manage.py runmcp`)

It reuses the desktop launcher's data-dir + SECRET_KEY handling so the MCP
server reads the SAME database and settings as the app window.

stdout is reserved for the MCP protocol — nothing here may print to it.
"""
import os
import sys
from pathlib import Path


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ.setdefault("DEBUG", "True")

    # Reuse the packaged app's persisted SECRET_KEY / writable data dir so this
    # process points at the same install. Safe no-op in a normal dev checkout.
    try:
        from desktop import _ensure_secret_key, _writable_data_dir

        _ensure_secret_key(_writable_data_dir())
    except Exception:
        pass

    import django

    django.setup()

    from mcp_server.server import mcp

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
