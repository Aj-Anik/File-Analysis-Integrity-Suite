"""
models/report.py

Data model for a single "report" - the recorded outcome of an operation
performed in any module (plagiarism check, compression job, duplicate scan).
Reports are the unit of storage for the History & Reports module.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


REPORT_TYPE_PLAGIARISM = "plagiarism"
REPORT_TYPE_COMPRESSION = "compression"
REPORT_TYPE_DUPLICATE = "duplicate"

VALID_REPORT_TYPES = {
    REPORT_TYPE_PLAGIARISM,
    REPORT_TYPE_COMPRESSION,
    REPORT_TYPE_DUPLICATE,
}


@dataclass
class Report:
    """
    A generic record of a single operation's result.

    Attributes:
        report_id: Unique identifier (UUID4 hex string).
        report_type: One of REPORT_TYPE_* constants.
        title: Short human-readable title, e.g. "essay1.txt vs essay2.txt".
        timestamp: ISO-format datetime string of when the operation completed.
        summary: Short one-line summary shown in list views.
        data: Arbitrary dict holding the full structured result
              (similarity scores, compression stats, duplicate groups, etc).
    """
    report_type: str
    title: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)
    report_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def __post_init__(self):
        if self.report_type not in VALID_REPORT_TYPES:
            raise ValueError(f"Invalid report_type: {self.report_type}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this Report to a plain dict for JSON persistence."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "title": self.title,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "data": self.data,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Report":
        """Reconstruct a Report instance from a dict (e.g. loaded from JSON)."""
        report = Report(
            report_type=data.get("report_type", REPORT_TYPE_PLAGIARISM),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            data=data.get("data", {}),
        )
        report.report_id = data.get("report_id", report.report_id)
        report.timestamp = data.get("timestamp", report.timestamp)
        return report

    def display_date(self) -> str:
        """Return a friendly date string for UI display."""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%d %b %Y, %I:%M %p")
        except ValueError:
            return self.timestamp
