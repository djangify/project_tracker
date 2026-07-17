import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Logs directory (matches Stream English behaviour).
# When packaged as a desktop .exe, BASE_DIR is a temporary, read-only
# PyInstaller extraction folder, so logs go next to the database instead
# (same writable folder as DATA_DIR in config/settings.py).
if getattr(sys, "frozen", False):
    LOGS_DIR = (
        Path(
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or Path.home()
        )
        / "ProjectTracker"
        / "logs"
    )
else:
    LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True, parents=True)

LOG_FILE = LOGS_DIR / "django.log"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_FILE,
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False,
        }
    },
}
