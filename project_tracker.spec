# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Project Tracker (desktop build).

Build from the project root, with the virtual environment active:

    pyinstaller project_tracker.spec

Output: dist/ProjectTracker/ProjectTracker.exe  (a one-folder app -- ship the
whole ProjectTracker folder)
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

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
    "google.generativeai",
]:
    p_datas, p_binaries, p_hidden = collect_all(pkg)
    datas += p_datas
    binaries += p_binaries
    hiddenimports += p_hidden

# Local Django apps + the project package. Django imports these by name at
# runtime, so PyInstaller can't discover them by following imports alone.
for pkg in ["config", "core", "crm", "pages", "projects", "assets", "products", "sequences"]:
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
for app in ["core", "crm", "pages", "projects", "assets", "products"]:
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


a = Analysis(
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

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ProjectTracker",
)
