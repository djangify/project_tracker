"""
Project Tracker desktop launcher.

Runs the Django app on a local production server (waitress) in a background
thread and displays it inside a native desktop window using PyWebView, so
users get an app window instead of a browser tab or a terminal command.

Run in development:   python desktop.py
Packaged as an .exe:  this file is the PyInstaller entry point (see
                       project_tracker.spec)
"""

import os
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


def _writable_data_dir() -> Path:
    """Match the DATA_DIR logic in config/settings.py so we can store a secret key."""
    if getattr(sys, "frozen", False):
        base = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or str(Path.home())
        )
        return Path(base) / "ProjectTracker"
    return Path(__file__).resolve().parent / "data"


def _ensure_secret_key(data_dir: Path) -> None:
    """
    Make sure a SECRET_KEY is available. In a packaged build there's no .env,
    so we generate one once and persist it in the user's data folder.
    """
    if os.environ.get("SECRET_KEY"):
        return
    if (Path(__file__).resolve().parent / ".env").exists() and not getattr(
        sys, "frozen", False
    ):
        # Dev run with a .env present -- let settings read it.
        return
    key_file = data_dir / "secret_key.txt"
    try:
        if key_file.exists():
            os.environ["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()
        else:
            from django.core.management.utils import get_random_secret_key

            key = get_random_secret_key()
            data_dir.mkdir(parents=True, exist_ok=True)
            key_file.write_text(key, encoding="utf-8")
            os.environ["SECRET_KEY"] = key
    except Exception:
        # Fall back to settings' built-in default if anything goes wrong.
        pass


def _resource_path(rel: str) -> str:
    """Resolve a bundled resource path (works in dev and in the frozen .exe)."""
    base = getattr(sys, "_MEIPASS", None) or str(Path(__file__).resolve().parent)
    return str(Path(base) / rel)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status < 500:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> None:
    # --- Environment: desktop mode, served locally over http on loopback ---
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["TRACKER_DESKTOP"] = "1"
    # DEBUG=True keeps things simple for a local single-user app: it serves
    # media files and avoids the HTTPS redirect that production mode forces.
    os.environ.setdefault("DEBUG", "True")

    data_dir = _writable_data_dir()
    _ensure_secret_key(data_dir)

    import django

    django.setup()

    # --- Apply any pending database migrations on startup ---
    from django.core.management import call_command

    try:
        call_command("migrate", interactive=False, verbosity=0)
    except Exception as exc:  # pragma: no cover - surfaced to the user
        print(f"Database setup failed: {exc}")

    # Make sure a login exists on a fresh install (demo@example.com /
    # admin123, or whatever DEFAULT_USER_EMAIL/DEFAULT_USER_PASSWORD are set
    # to). Safe to run every time -- it does nothing if a user already exists.
    try:
        call_command("create_default_user", verbosity=0)
    except Exception as exc:  # pragma: no cover
        print(f"Could not create the default user: {exc}")

    # Seed generic example content (prompt templates, sample assets, a
    # pre-filled voice profile, a finished example page) so a fresh install
    # has something to look at immediately, even before the user adds their
    # own ANTHROPIC_API_KEY. Idempotent -- get_or_create under the hood, so
    # this is a no-op after the first run.
    try:
        call_command("seed_examples", verbosity=0)
    except Exception as exc:  # pragma: no cover
        print(f"Could not seed example content: {exc}")

    # --- Start the web server in a background thread ---
    from waitress import serve
    from config.wsgi import application

    port = _find_free_port()
    host = "127.0.0.1"
    url = f"http://{host}:{port}/"

    server_thread = threading.Thread(
        target=lambda: serve(application, host=host, port=port, threads=8),
        daemon=True,
    )
    server_thread.start()

    if not _wait_until_ready(url + "health/", timeout=30):
        print("Project Tracker server did not start in time.")
        # Still try to open the window; it will show an error if truly dead.

    # --- Open the native window ---
    import webview

    webview.create_window(
        "Project Tracker",
        url,
        width=1280,
        height=860,
        min_size=(900, 600),
    )

    # Window icon. The bundled .exe already carries the icon (set in
    # project_tracker.spec); this also sets it where the GUI backend supports
    # it. Guarded so an unsupported backend can never stop the app launching.
    icon_path = _resource_path("static/images/favicon.ico")
    try:
        if os.path.exists(icon_path):
            webview.start(icon=icon_path)
        else:
            webview.start()
    except TypeError:
        # Older/unsupported backends don't accept the icon argument.
        webview.start()

    # Window closed -- exit immediately (daemon server thread is torn down).
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # console=False in the shipped build means errors normally vanish
        # with the window. This makes sure that never happens silently:
        # print the traceback and, if there's a console attached (debug
        # build), wait so it's actually readable before the window closes.
        import traceback

        traceback.print_exc()
        try:
            input("\nProject Tracker failed to start. Press Enter to close...")
        except Exception:
            pass
        raise
