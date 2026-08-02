"""Shared application logging for PawPal+.

Provides a single get_logger(name) entry point used by retrieval.py,
validators.py, and ai_assistant.py. Only the standard library `logging`
module is used - no third-party logging dependency.

Design notes:

- All PawPal+ loggers hang off one shared "pawpal_ai" logger that owns the
  actual handlers (console + rotating-free file). Module loggers returned by
  get_logger() are children of it and add no handlers of their own. A
  module-level flag tracks whether that shared logger has been configured
  yet, so calling get_logger() many times (including across Streamlit
  reruns, which re-run this module's top-level code in the same process)
  never creates duplicate handlers or duplicate log lines.
- The shared logger has `propagate = False`, so PawPal+ log records never
  reach the root logger. This keeps logging.basicConfig()-style setup fully
  scoped to this application and leaves any other library's logging
  configuration untouched.
- Setting up the log file is best-effort: if the logs directory or file
  cannot be created (read-only filesystem, permissions, etc.) PawPal+ keeps
  running with console-only logging instead of crashing.
"""

import logging
import os

LOG_DIR = "logs"
LOG_FILE_NAME = "pawpal_ai.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

_APP_LOGGER_NAME = "pawpal_ai"

_configured = False


def _configure_app_logger():
    """Attach console/file handlers to the shared PawPal+ logger exactly
    once per process. Safe to call any number of times."""
    global _configured

    app_logger = logging.getLogger(_APP_LOGGER_NAME)

    if _configured:
        return app_logger

    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)
    except OSError:
        app_logger.warning(
            "Could not set up file logging (logs directory/file unavailable); "
            "continuing with console logging only."
        )

    _configured = True
    return app_logger


def get_logger(name):
    """Return a PawPal+ logger for `name` (typically module __name__).

    Guarantees the shared console/file handlers exist exactly once per
    process, so repeated calls - including Streamlit reruns - never produce
    duplicate log lines. Never raises: a broken log directory/file falls
    back to console-only logging rather than crashing the caller.
    """
    _configure_app_logger()
    return logging.getLogger(f"{_APP_LOGGER_NAME}.{name}")
