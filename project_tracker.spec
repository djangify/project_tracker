# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Project Tracker (desktop build).

Build from the project root, with the virtual environment active:

    pyinstaller project_tracker.spec

Output: dist/ProjectTracker/ with TWO executables:
  - ProjectTracker.exe      the app window (windowed)
  - ProjectTracker-mcp.exe  the MCP server for Claude Desktop (console — stdio
                            needs real stdin/stdout, which a windowed exe lacks)

Ship the whole ProjectTracker folder. Claude Desktop is pointed at
ProjectTracker-mcp.exe automatically on first launch (see desktop.py /
mcp_server/desktop_connect.py).
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Packages that load templates / static / submodules dynamically and
# therefore need everything bundled (collect_all = data files + binaries +
# submodules).
for pkg in [
    "django",
    "rest_framework",
    "adminita",
    "corsheaders",
    "whitenoise",
    "waitress",
    "webview",
    "anthropic",
    "openai",
    "google.genai",   # new Google GenAI SDK (replaces google-generativeai)
]:
    p_datas, p_binaries, p_hidden = collect_all(pkg)
    datas += p_datas
    binaries += p_binaries
    hiddenimports += p_hidden

# MCP SDK: collect only the server/client/shared subpackages, NOT mcp.cli.
# mcp.cli imports the optional 'typer' dependency and calls sys.exit(1) at
# import time when it's missing, which crashes a whole-package collect_all.
for sub in ["mcp.server", "mcp.client", "mcp.shared"]:
    hiddenimports += collect_submodules(sub)
hiddenimports += ["mcp", "mcp.types"]
datas += collect_data_files("mcp")

# Local Django apps + the project package. Django imports these by name at
# runtime, so PyInstaller can't discover them by following imports alone.
for pkg in [
    "config", "core", "crm", "pages", "projects", "assets", "products",
    "sequences", "content_calendar", "ai_settings", "ai_assistant", "mcp_server",
]:
    hiddenimports += collect_submodules(pkg)

# Project-level templates and static source files.
datas += [
    ("templates", "templates"),
    ("static", "static"),
]

# Each local app's own templates/ folder (Django's app_directories loader
# expects <app>/templates/<app>/*.html on disk). collect_submodules() only
# grabs .py files, so these non-Python assets have to be listed explicitly
# or the packaged app 500s with TemplateDoesNotExist.
for app in [
    "core", "crm", "pages", "projects", "assets", "products",
    "content_calendar", "ai_settings", "ai_assistant",
]:
    datas += [(f"{app}/templates", f"{app}/templates")]

# core/templatetags is a package but also gets used via {% load %} in
# templates -- make sure it's importable as a submodule too (belt and
# braces alongside the collect_submodules("core") call above).
hiddenimports += ["core.templatetags"]

# Modules that Project Tracker references by string name (in settings:
# MIDDLEWARE, context processors, ROOT_URLCONF, included urlconfs).
# PyInstaller can't see these by following imports, so they must be listed
# explicitly.
hiddenimports += [
    "config.settings",
    "config.urls",
    "config.wsgi",
    "config.views",
    "core.urls",
    "core.views",
    "core.apps",
    "core.context_processors",
    "crm.urls",
    "crm.views",
    "crm.apps",
    "pages.urls",
    "pages.views",
    "pages.apps",
    "pages.context_processors",
    "projects.urls",
    "projects.views",
    "projects.apps",
    "projects.serializers",
    "crm.serializers",
    "assets.urls",
    "assets.views",
    "assets.apps",
    "assets.services",
    "products.urls",
    "products.views",
    "products.apps",
    "sequences.apps",
    # --- Content OS apps (content calendar + AI settings/assistant + MCP) ---
    "content_calendar.apps",
    "content_calendar.urls",
    "content_calendar.views",
    "content_calendar.serializers",
    "content_calendar.forms",
    "content_calendar.generation",
    "content_calendar.models",
    "ai_settings.apps",
    "ai_settings.urls",
    "ai_settings.views",
    "ai_settings.ai_client",
    "ai_settings.encryption",
    "ai_settings.models",
    "ai_assistant.apps",
    "ai_assistant.urls",
    "ai_assistant.views",
    "ai_assistant.agent",
    "ai_assistant.tools",
    "mcp_server.server",
    "mcp_server.desktop_connect",
    "anthropic",
]

# Lazily-imported bits that the analyzer can miss.
hiddenimports += [
    "environ",
    "PIL",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.humanize.templatetags.humanize",
]


# --- Analysis 1: the app window (entry point desktop.py) -------------------
a_app = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_app = PYZ(a_app.pure)
exe_app = EXE(
    pyz_app,
    a_app.scripts,
    [],
    exclude_binaries=True,
    name="ProjectTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static/images/favicon.ico",
)

# --- Analysis 2: the MCP server (entry point mcp_launcher.py) ---------------
# Console subsystem: MCP stdio needs real stdin/stdout, which a windowed exe
# does not have. Claude Desktop launches this with piped std handles.
a_mcp = Analysis(
    ["mcp_launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_mcp = PYZ(a_mcp.pure)
exe_mcp = EXE(
    pyz_mcp,
    a_mcp.scripts,
    [],
    exclude_binaries=True,
    name="ProjectTracker-mcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static/images/favicon.ico",
)

# Collect both executables and their (deduplicated) dependencies into one
# shippable folder.
coll = COLLECT(
    exe_app,
    exe_mcp,
    a_app.binaries,
    a_app.datas,
    a_mcp.binaries,
    a_mcp.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ProjectTracker",
)
