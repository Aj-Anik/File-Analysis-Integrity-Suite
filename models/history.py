"""
models/history.py

Implements the persistence and in-memory data-structure layer for the
History & Reports module.

This file explicitly demonstrates several DSA concepts required by the
project specification:

    * Stack   -> UndoStack: supports undoing the most recent "delete report"
                 operation (LIFO).
    * Queue   -> RecentActivityQueue: a bounded FIFO queue of the most
                 recently performed operations, used to drive a
                 "Recent Activity" panel in the UI.
    * List    -> HistoryManager keeps the master record list and persists
                 it to a JSON file on disk (acts as the long-term store
                 backing the Stack/Queue views above).

All persistence is plain JSON under data/history/.
"""

import json
import os
from collections import deque
from typing import List, Optional

from models.report import Report


HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "history")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")

RECENT_ACTIVITY_MAXLEN = 15


class UndoStack:
    """
    A classic LIFO stack used to support "Undo last delete" in the
    History & Reports screen.
    """

    def __init__(self):
        self._stack: List[Report] = []

    def push(self, report: Report) -> None:
        """Push a deleted report onto the stack so it can later be restored."""
        self._stack.append(report)

    def pop(self) -> Optional[Report]:
        """Pop the most recently deleted report off the stack (LIFO)."""
        if not self._stack:
            return None
        return self._stack.pop()

    def peek(self) -> Optional[Report]:
        """Return the top of the stack without removing it."""
        if not self._stack:
            return None
        return self._stack[-1]

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def __len__(self) -> int:
        return len(self._stack)


class RecentActivityQueue:
    """
    A bounded FIFO queue (implemented with collections.deque) holding the
    most recent operations performed across all modules. Oldest entries
    are automatically evicted once the queue exceeds RECENT_ACTIVITY_MAXLEN.
    """

    def __init__(self, maxlen: int = RECENT_ACTIVITY_MAXLEN):
        self._queue: deque = deque(maxlen=maxlen)

    def enqueue(self, report: Report) -> None:
        """Add a new report to the back of the queue (FIFO)."""
        self._queue.append(report)

    def dequeue(self) -> Optional[Report]:
        """Remove and return the oldest report in the queue."""
        if not self._queue:
            return None
        return self._queue.popleft()

    def to_list(self) -> List[Report]:
        """Return the queue contents as a list, most-recent first (for display)."""
        return list(reversed(self._queue))

    def __len__(self) -> int:
        return len(self._queue)


class HistoryManager:
    """
    Top-level manager that owns:
        * The master list of all Report objects (persisted to JSON).
        * A RecentActivityQueue mirroring the most recent operations.
        * An UndoStack for restoring accidentally deleted reports.

    This is the single source of truth that the UI's History & Reports
    tab reads from and writes to.
    """

    def __init__(self, history_file: str = HISTORY_FILE):
        self.history_file = history_file
        self._reports: List[Report] = []
        self.recent_activity = RecentActivityQueue()
        self.undo_stack = UndoStack()
        self._ensure_storage()
        self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load(self) -> None:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._reports = [Report.from_dict(item) for item in raw]
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            self._reports = []
        # Rebuild the recent-activity queue from the tail of the saved history
        for report in self._reports[-RECENT_ACTIVITY_MAXLEN:]:
            self.recent_activity.enqueue(report)

    def _save(self) -> None:
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self._reports], f, indent=2)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def add_report(self, report: Report) -> None:
        """Record a new report: append to master list, push to recent queue, persist."""
        self._reports.append(report)
        self.recent_activity.enqueue(report)
        self._save()

    def get_all_reports(self) -> List[Report]:
        """Return all reports, most recent first."""
        return list(reversed(self._reports))

    def get_reports_by_type(self, report_type: str) -> List[Report]:
        """Return all reports of a given type, most recent first."""
        return [r for r in reversed(self._reports) if r.report_type == report_type]

    def search_reports(self, query: str) -> List[Report]:
        """
        Linear search across report titles and summaries (case-insensitive).
        Demonstrates a basic search algorithm over the in-memory report list.
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return self.get_all_reports()
        results = []
        for report in reversed(self._reports):
            if query_lower in report.title.lower() or query_lower in report.summary.lower():
                results.append(report)
        return results

    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report by id. The deleted report is pushed onto the
        UndoStack so it can be restored with undo_delete().
        Returns True if a report was found and deleted.
        """
        for i, report in enumerate(self._reports):
            if report.report_id == report_id:
                removed = self._reports.pop(i)
                self.undo_stack.push(removed)
                self._save()
                return True
        return False

    def undo_delete(self) -> Optional[Report]:
        """
        Pop the most recently deleted report off the UndoStack and restore
        it to the master list. Returns the restored Report, or None if the
        undo stack was empty.
        """
        restored = self.undo_stack.pop()
        if restored is None:
            return None
        self._reports.append(restored)
        self.recent_activity.enqueue(restored)
        self._save()
        return restored

    def get_report(self, report_id: str) -> Optional[Report]:
        """Look up a single report by its id."""
        for report in self._reports:
            if report.report_id == report_id:
                return report
        return None

    def clear_all(self) -> None:
        """Remove all history (used by 'Clear History' button)."""
        self._reports = []
        self.recent_activity = RecentActivityQueue()
        self._save()

    def get_recent_activity(self) -> List[Report]:
        """Return the recent-activity queue contents, most recent first."""
        return self.recent_activity.to_list()

    def stats(self) -> dict:
        """Aggregate counts per report type, used by the Statistics Dashboard."""
        counts = {"plagiarism": 0, "compression": 0, "duplicate": 0}
        for r in self._reports:
            if r.report_type in counts:
                counts[r.report_type] += 1
        counts["total"] = len(self._reports)
        return counts
