"""
ui/widgets.py

Small reusable custom widgets shared across multiple tabs:
    * StatCard          - a labelled number tile for dashboards
    * DropZoneLabel     - a drag-and-drop enabled file drop target
    * SimilarityGauge   - a circular gauge widget for the plagiarism score
"""

from typing import Callable, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class StatCard(QFrame):
    """A small dashboard tile showing a big number and a caption underneath."""

    def __init__(self, title: str, value: str = "0", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(86)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")

        self.caption_label = QLabel(title)
        self.caption_label.setObjectName("StatCaption")

        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class DropZoneLabel(QLabel):
    """
    A QLabel subclass that accepts drag-and-drop of files from the OS
    file explorer. Calls `on_file_dropped(path)` with the first dropped
    file's absolute path.

    Used by the Plagiarism Detector (drop a .txt/.docx/.pdf) and the
    File Compression module (drop any file to compress/decompress).
    """

    file_dropped = pyqtSignal(str)

    def __init__(self, placeholder_text: str, allowed_extensions: Optional[List[str]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(placeholder_text, parent)
        self.allowed_extensions = [e.lower() for e in allowed_extensions] if allowed_extensions else None
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(110)
        self._default_style = (
            "QLabel { border: 2px dashed #9AA5E0; border-radius: 10px; "
            "color: #6B7290; padding: 14px; background-color: rgba(120,140,230,0.06); }"
        )
        self._hover_style = (
            "QLabel { border: 2px dashed #3E50B4; border-radius: 10px; "
            "color: #2E3A87; padding: 14px; background-color: rgba(120,140,230,0.14); }"
        )
        self.setStyleSheet(self._default_style)
        self.placeholder_text = placeholder_text

    def _is_allowed(self, path: str) -> bool:
        if self.allowed_extensions is None:
            return True
        return any(path.lower().endswith(ext) for ext in self.allowed_extensions)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_allowed(urls[0].toLocalFile()):
                self.setStyleSheet(self._hover_style)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setStyleSheet(self._default_style)
        urls = event.mimeData().urls()
        if not urls:
            return
        local_path = urls[0].toLocalFile()
        if self._is_allowed(local_path):
            self.setText(f"Selected:\n{local_path}")
            self.file_dropped.emit(local_path)
        else:
            self.setText("Unsupported file type. " + self.placeholder_text)

    def reset_text(self) -> None:
        self.setText(self.placeholder_text)


class SimilarityGauge(QWidget):
    """
    A simple circular gauge that fills proportionally to a 0-100 percentage,
    used as the headline visual for the Plagiarism Detector's result panel.
    Color shifts from green (low similarity) to red (high similarity).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._value = 0.0
        self.setMinimumSize(140, 140)

    def set_value(self, percent: float) -> None:
        self._value = max(0.0, min(100.0, percent))
        self.update()

    def _color_for_value(self) -> QColor:
        if self._value < 30:
            return QColor("#3FAE5C")    # green - low similarity, likely original
        elif self._value < 60:
            return QColor("#E0A93E")    # amber - moderate similarity
        else:
            return QColor("#D4453A")    # red - high similarity, possible plagiarism

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height()) - 20
        rect_x = (self.width() - side) // 2
        rect_y = (self.height() - side) // 2

        # Background ring
        pen_bg = QPen(QColor("#E3E7F3"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect_x, rect_y, side, side, 0, 360 * 16)

        # Foreground value ring
        pen_fg = QPen(self._color_for_value(), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        span_angle = int(-self._value / 100 * 360 * 16)
        painter.drawArc(rect_x, rect_y, side, side, 90 * 16, span_angle)

        # Center text
        painter.setPen(QColor("#1E2233"))
        font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value:.1f}%")

        painter.end()
