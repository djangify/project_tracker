# mcp_server/desktop_connect.py
"""Register this install as an MCP server in the user's Claude Desktop config.

Lets a fresh install connect to Claude Desktop automatically on first launch,
so a non-technical owner never has to hand-edit a JSON file. Everything here is
best-effort and must never raise into the app's startup path — callers get a
short status string instead.

There is no "account" to connect to: an MCP server is just a local config entry
telling Claude Desktop which program to launch. So this is safe and reversible —
the owner can remove the entry in Claude Desktop at any time.
"""
import json
import os
import sys
from pathlib import Path

SERVER_NAME = "content-calendar"


def claude_config_path() -> Path | None:
    """Location of claude_desktop_config.json for this OS, or None if unknown."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    # Linux (community Claude Desktop builds) — best effort.
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def claude_desktop_present(config_path: Path | None = None) -> bool:
    """True if Claude Desktop looks installed (its config directory exists)."""
    path = config_path or claude_config_path()
    return bool(path and path.parent.exists())


def server_entry(base_dir: Path, frozen: bool) -> dict:
    """The mcpServers entry to install — correct for a packaged .exe vs dev."""
    if frozen:
        # Packaged: point at the sibling console MCP executable that
        # project_tracker.spec builds next to the main app .exe.
        folder = Path(sys.executable).resolve().parent
        exe_name = "ProjectTracker-mcp.exe" if sys.platform == "win32" else "ProjectTracker-mcp"
        return {"command": str(folder / exe_name), "args": [], "cwd": str(folder)}
    # Dev: use the current interpreter to run the management command.
    return {"command": sys.executable, "args": ["manage.py", "runmcp"], "cwd": str(base_dir)}


def connect(base_dir: Path, frozen: bool, *, config_path: Path | None = None,
            name: str = SERVER_NAME) -> str:
    """Merge the server entry into Claude Desktop's config.

    Returns one of: 'connected' (newly added), 'updated' (changed to match this
    install), 'unchanged' (already correct), 'no-claude' (Claude Desktop not
    found), or 'error: <reason>'. Never raises. Preserves all other config keys,
    and refuses to overwrite a config file it can't parse.
    """
    try:
        cfg_path = config_path or claude_config_path()
        if not cfg_path or not cfg_path.parent.exists():
            return "no-claude"

        cfg = {}
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8")) or {}
            except (json.JSONDecodeError, OSError):
                # Don't clobber a file we can't understand.
                return "error: existing Claude config could not be read"
            if not isinstance(cfg, dict):
                return "error: existing Claude config is not an object"

        servers = cfg.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            return "error: existing mcpServers is not an object"

        desired = server_entry(base_dir, frozen)
        if servers.get(name) == desired:
            return "unchanged"

        status = "updated" if name in servers else "connected"
        servers[name] = desired
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return status
    except Exception as exc:  # noqa: BLE001 — must never break app startup
        return f"error: {exc}"
