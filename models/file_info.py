"""
models/file_info.py

Simple data model representing metadata about a file on disk.
Used by the Duplicate File Finder module.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileInfo:
    """
    Represents a single file discovered during a directory scan.

    Attributes:
        path: Absolute path to the file.
        size: Size of the file in bytes.
        file_hash: SHA-256 hex digest of the file's contents (computed lazily).
        modified_time: Last modification timestamp (ISO format string).
    """
    path: str
    size: int
    file_hash: str = ""
    modified_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Serialize this FileInfo to a plain dict for JSON persistence."""
        return {
            "path": self.path,
            "size": self.size,
            "file_hash": self.file_hash,
            "modified_time": self.modified_time,
        }

    @staticmethod
    def from_dict(data: dict) -> "FileInfo":
        """Reconstruct a FileInfo instance from a dict (e.g. loaded from JSON)."""
        return FileInfo(
            path=data.get("path", ""),
            size=data.get("size", 0),
            file_hash=data.get("file_hash", ""),
            modified_time=data.get("modified_time", ""),
        )

    def human_size(self) -> str:
        """Return a human-readable string for the file size (e.g. '1.4 MB')."""
        size = float(self.size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
