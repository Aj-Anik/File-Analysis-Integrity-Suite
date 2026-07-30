"""
ui/history_ui.py

Module 4: History & Reports tab.

Surfaces the HistoryManager (models/history.py) to the user:
    * Statistics dashboard (counts per report type)
    * Search box (linear/fuzzy substring search across all reports)
    * Sortable list of all saved reports
    * View full report details
    * Delete report (pushes onto UndoStack) + "Undo Last Delete" button
    * Export any report back out to PDF
    * Recent Activity panel (backed by the Queue)
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QMessageBox, QListWidget, QListWidgetItem, QFileDialog,
    QSplitter, QTextEdit, QComboBox,
)

from algorithms.pdf_export import export_report
from algorithms.search_sort import fuzzy_substring_search, merge_sort
from models.history import HistoryManager
from models.report import (
    Report, REPORT_TYPE_PLAGIARISM, REPORT_TYPE_COMPRESSION, REPORT_TYPE_DUPLICATE,
)
from ui.widgets import StatCard
from utils.paths import ensure_reports_dir


_TYPE_LABELS = {
    REPORT_TYPE_PLAGIARISM: "Plagiarism Check",
    REPORT_TYPE_COMPRESSION: "Compression",
    REPORT_TYPE_DUPLICATE: "Duplicate Scan",
}


class HistoryTab(QWidget):
    """Top-level widget for the History & Reports module."""

    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.current_reports = []  # currently displayed (filtered/sorted) list
        self.selected_report = None
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel("History & Reports")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Browse, search, and manage every operation you've run across all modules.")
        subtitle.setObjectName("PageSubtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        # --- Stats dashboard ---
        stats_row = QHBoxLayout()
        self.total_card = StatCard("Total Records", "0")
        self.plag_card = StatCard("Plagiarism Checks", "0")
        self.comp_card = StatCard("Compressions", "0")
        self.dup_card = StatCard("Duplicate Scans", "0")
        for card in (self.total_card, self.plag_card, self.comp_card, self.dup_card):
            stats_row.addWidget(card)
        outer.addLayout(stats_row)

        # --- Toolbar: search + filter + undo + clear ---
        toolbar = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by title or summary...")
        self.search_box.textChanged.connect(self.refresh)
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Types", None)
        self.filter_combo.addItem("Plagiarism Checks", REPORT_TYPE_PLAGIARISM)
        self.filter_combo.addItem("Compression Jobs", REPORT_TYPE_COMPRESSION)
        self.filter_combo.addItem("Duplicate Scans", REPORT_TYPE_DUPLICATE)
        self.filter_combo.currentIndexChanged.connect(self.refresh)

        self.undo_btn = QPushButton("Undo Last Delete")
        self.undo_btn.setObjectName("SecondaryButton")
        self.undo_btn.clicked.connect(self.on_undo_delete)
        self.clear_btn = QPushButton("Clear All History")
        self.clear_btn.setObjectName("DangerButton")
        self.clear_btn.clicked.connect(self.on_clear_all)

        toolbar.addWidget(self.search_box, 2)
        toolbar.addWidget(self.filter_combo, 1)
        toolbar.addWidget(self.undo_btn)
        toolbar.addWidget(self.clear_btn)
        outer.addLayout(toolbar)

        # --- Split view: list on left, details on right ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        list_frame = QFrame()
        list_frame.setObjectName("ContentCard")
        list_layout = QVBoxLayout(list_frame)
        list_label = QLabel("All Reports")
        list_label.setObjectName("SectionLabel")
        list_layout.addWidget(list_label)
        self.report_list = QListWidget()
        self.report_list.currentItemChanged.connect(self.on_report_selected)
        list_layout.addWidget(self.report_list)

        list_action_row = QHBoxLayout()
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.clicked.connect(self.on_delete_report)
        self.export_btn = QPushButton("Export as PDF")
        self.export_btn.setObjectName("SecondaryButton")
        self.export_btn.clicked.connect(self.on_export_report)
        list_action_row.addWidget(self.delete_btn)
        list_action_row.addWidget(self.export_btn)
        list_layout.addLayout(list_action_row)

        detail_frame = QFrame()
        detail_frame.setObjectName("ContentCard")
        detail_layout = QVBoxLayout(detail_frame)
        detail_label = QLabel("Report Details")
        detail_label.setObjectName("SectionLabel")
        detail_layout.addWidget(detail_label)
        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        detail_layout.addWidget(self.detail_box)

        recent_label = QLabel("Recent Activity")
        recent_label.setObjectName("SectionLabel")
        detail_layout.addWidget(recent_label)
        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(140)
        detail_layout.addWidget(self.recent_list)

        splitter.addWidget(list_frame)
        splitter.addWidget(detail_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        """Re-pull data from HistoryManager, apply search/filter/sort, and redraw."""
        all_reports = self.history_manager.get_all_reports()

        # Apply type filter
        selected_type = self.filter_combo.currentData()
        if selected_type:
            all_reports = [r for r in all_reports if r.report_type == selected_type]

        # Apply fuzzy search (over title + summary combined)
        query = self.search_box.text().strip()
        if query:
            all_reports = fuzzy_substring_search(all_reports, query, key=lambda r: f"{r.title} {r.summary}")

        # Sort newest-first by timestamp using our own merge_sort implementation
        all_reports = merge_sort(all_reports, key=lambda r: r.timestamp, reverse=True)
        self.current_reports = all_reports

        self.report_list.clear()
        for report in all_reports:
            type_label = _TYPE_LABELS.get(report.report_type, report.report_type)
            item_text = f"[{type_label}]  {report.title}\n{report.summary}  -  {report.display_date()}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, report.report_id)
            self.report_list.addItem(item)

        # Stats dashboard
        stats = self.history_manager.stats()
        self.total_card.set_value(str(stats["total"]))
        self.plag_card.set_value(str(stats["plagiarism"]))
        self.comp_card.set_value(str(stats["compression"]))
        self.dup_card.set_value(str(stats["duplicate"]))

        # Recent activity (Queue)
        self.recent_list.clear()
        for report in self.history_manager.get_recent_activity():
            type_label = _TYPE_LABELS.get(report.report_type, report.report_type)
            self.recent_list.addItem(f"[{type_label}] {report.title} - {report.display_date()}")

        self.detail_box.clear()
        self.selected_report = None

    def on_report_selected(self, current, _previous) -> None:
        if current is None:
            self.selected_report = None
            self.detail_box.clear()
            return
        report_id = current.data(Qt.ItemDataRole.UserRole)
        report = self.history_manager.get_report(report_id)
        self.selected_report = report
        if report is None:
            self.detail_box.clear()
            return

        lines = [
            f"<b>Type:</b> {_TYPE_LABELS.get(report.report_type, report.report_type)}",
            f"<b>Title:</b> {report.title}",
            f"<b>Summary:</b> {report.summary}",
            f"<b>Date:</b> {report.display_date()}",
            "<hr>",
        ]
        for key, value in report.data.items():
            if isinstance(value, (list, dict)):
                continue  # keep detail view concise; full data is in the exported PDF
            lines.append(f"<b>{key.replace('_', ' ').title()}:</b> {value}")
        self.detail_box.setHtml("<br>".join(lines))

    # ------------------------------------------------------------------ #
    def on_delete_report(self) -> None:
        if not self.selected_report:
            QMessageBox.warning(self, "No Selection", "Select a report from the list first.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete this report?\n\n{self.selected_report.title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.delete_report(self.selected_report.report_id)
            self.refresh()

    def on_undo_delete(self) -> None:
        restored = self.history_manager.undo_delete()
        if restored is None:
            QMessageBox.information(self, "Nothing to Undo", "There are no deleted reports to restore.")
        else:
            QMessageBox.information(self, "Restored", f"Restored report: {restored.title}")
            self.refresh()

    def on_clear_all(self) -> None:
        reply = QMessageBox.question(
            self, "Confirm Clear All",
            "This will permanently delete ALL history records (not the undo stack). Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.clear_all()
            self.refresh()

    def on_export_report(self) -> None:
        if not self.selected_report:
            QMessageBox.warning(self, "No Selection", "Select a report from the list first.")
            return
        default_name = f"{self.selected_report.report_type}_report.pdf"
        default_path = os.path.join(ensure_reports_dir(), default_name)
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        try:
            export_report(self.selected_report, path)
            QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF:\n{e}")

    def add_report(self, report: Report) -> None:
        """Called externally (e.g. from MainWindow) whenever another tab emits report_created."""
        self.history_manager.add_report(report)
        self.refresh()
