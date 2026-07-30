"""
utils/paths.py

Shared path constants used across the application, so every module
agrees on where persistent data lives relative to the project root,
regardless of the current working directory the app was launched from.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + "utils", 1)[0]
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
HISTORY_DIR = os.path.join(DATA_DIR, "history")


def ensure_reports_dir() -> str:
    """Create data/reports/ if it doesn't exist yet, and return its path."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR
