"""
ui/duplicate_ui.py

Module 3: Duplicate File Finder tab.

Lets the user pick a folder, recursively scans it, groups files by size
then by SHA-256 content hash (see algorithms/duplicate_detector.py), and
displays duplicate groups in an interactive tree-like table. Supports
deleting selected duplicate files (with confirmation) and exporting a
PDF summary report.
"""

import os

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QFrame, QProgressBar, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QScrollArea, QCheckBox,
)

from algorithms.duplicate_detector import scan_and_find_duplicates
from algorithms.pdf_export import export_duplicate_report
from models.report import Report, REPORT_TYPE_DUPLICATE
from ui.widgets import StatCard
from utils.paths import ensure_reports_dir


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


class DuplicateScanWorker(QThread):
    progress = pyqtSignal(str, int, int)  # phase ("scan"/"hash"), current, total
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, root_dir: str):
        super().__init__()
        self.root_dir = root_dir

    def run(self) -> None:
        try:
            result = scan_and_find_duplicates(
                self.root_dir,
                scan_progress_callback=lambda cur, tot: self.progress.emit("scan", cur, tot),
                hash_progress_callback=lambda cur, tot: self.progress.emit("hash", cur, tot),
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class DuplicateTab(QWidget):
    """Top-level widget for the Duplicate File Finder module."""

    report_created = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_dir = None
        self.last_result = None
        self.worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel("Duplicate File Finder")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Scan a folder recursively and detect duplicate files using SHA-256 "
                           "content hashing, grouped via hash tables for fast lookup.")
        subtitle.setObjectName("PageSubtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setSpacing(14)
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        # --- Input card ---
        input_card = QFrame()
        input_card.setObjectName("ContentCard")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 18, 20, 18)
        input_layout.setSpacing(10)

        folder_row = QHBoxLayout()
        self.folder_label = QLabel("No folder selected.")
        self.folder_label.setWordWrap(True)
        select_btn = QPushButton("Select Folder...")
        select_btn.setObjectName("SecondaryButton")
        select_btn.clicked.connect(self.on_select_folder)
        folder_row.addWidget(self.folder_label, 1)
        folder_row.addWidget(select_btn)
        input_layout.addLayout(folder_row)

        action_row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan for Duplicates")
        self.scan_btn.setObjectName("PrimaryButton")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        action_row.addWidget(self.scan_btn)
        action_row.addStretch()
        input_layout.addLayout(action_row)

        self.progress_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_label)
        input_layout.addWidget(self.progress_bar)

        scroll_layout.addWidget(input_card)

        # --- Summary stats ---
        self.results_card = QFrame()
        self.results_card.setObjectName("ContentCard")
        self.results_card.setVisible(False)
        self._build_results_section()
        scroll_layout.addWidget(self.results_card)
        scroll_layout.addStretch()

    def _build_results_section(self) -> None:
        layout = QVBoxLayout(self.results_card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        results_title = QLabel("Scan Results")
        results_title.setObjectName("SectionLabel")
        header_row.addWidget(results_title)
        header_row.addStretch()
        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.setObjectName("SecondaryButton")
        self.export_pdf_btn.clicked.connect(self.on_export_pdf)
        self.save_history_btn = QPushButton("Save to History")
        self.save_history_btn.setObjectName("SecondaryButton")
        self.save_history_btn.clicked.connect(self.on_save_to_history)
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setObjectName("DangerButton")
        self.delete_selected_btn.clicked.connect(self.on_delete_selected)
        header_row.addWidget(self.export_pdf_btn)
        header_row.addWidget(self.save_history_btn)
        header_row.addWidget(self.delete_selected_btn)
        layout.addLayout(header_row)

        stats_row = QHBoxLayout()
        self.scanned_card = StatCard("Files Scanned", "0")
        self.groups_card = StatCard("Duplicate Groups", "0")
        self.dupfiles_card = StatCard("Duplicate Files", "0")
        self.wasted_card = StatCard("Wasted Storage", "0 B")
        for card in (self.scanned_card, self.groups_card, self.dupfiles_card, self.wasted_card):
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        hint = QLabel("Tick the files you want to remove, then click 'Delete Selected'. "
                      "One copy per group is always kept unticked by default.")
        hint.setObjectName("StatCaption")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Select", "File Path", "Size"])
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.setMinimumHeight(320)
        layout.addWidget(self.tree)

    # ------------------------------------------------------------------ #
    def on_select_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if path:
            self.selected_dir = path
            self.folder_label.setText(f"<b>Selected folder:</b> {path}")

    def on_scan_clicked(self) -> None:
        if not self.selected_dir:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder to scan first.")
            return

        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Scanning directory...")

        self.worker = DuplicateScanWorker(self.selected_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.failed.connect(self._on_scan_failed)
        self.worker.start()

    def _on_progress(self, phase: str, current: int, total: int) -> None:
        total = max(total, 1)
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)
        label = "Scanning files..." if phase == "scan" else "Hashing candidate duplicates..."
        self.progress_label.setText(f"{label} ({current}/{total})")

    def _on_scan_finished(self, result: dict) -> None:
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Scan complete.")
        self.last_result = result
        self.results_card.setVisible(True)

        self.scanned_card.set_value(str(result["total_files_scanned"]))
        self.groups_card.set_value(str(result["duplicate_groups_count"]))
        self.dupfiles_card.set_value(str(result["duplicate_files_count"]))
        self.wasted_card.set_value(_human_size(result["wasted_bytes"]))

        self.tree.clear()
        for i, (file_hash, group) in enumerate(result["duplicate_groups"].items(), start=1):
            parent_item = QTreeWidgetItem(["", f"Group {i} ({len(group)} files) - hash {file_hash[:10]}...", ""])
            parent_item.setFlags(parent_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self.tree.addTopLevelItem(parent_item)
            for j, file_info in enumerate(group):
                child = QTreeWidgetItem(["", file_info.path, file_info.human_size()])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                # Keep the first file in each group unchecked by default (the "keeper")
                child.setCheckState(0, Qt.CheckState.Unchecked if j == 0 else Qt.CheckState.Checked)
                parent_item.addChild(child)
            parent_item.setExpanded(True)

        if result["duplicate_groups_count"] == 0:
            QMessageBox.information(self, "Scan Complete", "No duplicate files were found in this folder.")

    def _on_scan_failed(self, error_msg: str) -> None:
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Scan Failed", f"An error occurred while scanning:\n{error_msg}")

    # ------------------------------------------------------------------ #
    def on_delete_selected(self) -> None:
        if not self.last_result:
            return

        to_delete = []
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            for j in range(group_item.childCount()):
                child = group_item.child(j)
                if child.checkState(0) == Qt.CheckState.Checked:
                    to_delete.append(child.text(1))

        if not to_delete:
            QMessageBox.information(self, "Nothing Selected", "No files are checked for deletion.")
            return

        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"You are about to permanently delete {len(to_delete)} file(s). This cannot be undone.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted, errors = 0, []
        for path in to_delete:
            try:
                os.remove(path)
                deleted += 1
            except OSError as e:
                errors.append(f"{path}: {e}")

        msg = f"Deleted {deleted} of {len(to_delete)} file(s)."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:10])
        QMessageBox.information(self, "Deletion Complete", msg)

        # Re-scan to refresh the view after deletion
        self.on_scan_clicked()

    # ------------------------------------------------------------------ #
    def on_export_pdf(self) -> None:
        if not self.last_result:
            return
        default_path = os.path.join(ensure_reports_dir(), "duplicate_report.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        report = self._build_report()
        try:
            export_duplicate_report(report, path)
            QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF:\n{e}")

    def on_save_to_history(self) -> None:
        if not self.last_result:
            return
        report = self._build_report()
        self.report_created.emit(report)
        QMessageBox.information(self, "Saved", "This scan result has been saved to History & Reports.")

    def _build_report(self) -> Report:
        result = self.last_result
        groups_preview = [
            [f.path for f in group] for group in list(result["duplicate_groups"].values())[:20]
        ]
        data = {
            "root_dir": result["root_dir"],
            "total_files_scanned": result["total_files_scanned"],
            "duplicate_groups_count": result["duplicate_groups_count"],
            "duplicate_files_count": result["duplicate_files_count"],
            "wasted_bytes": result["wasted_bytes"],
            "wasted_human": _human_size(result["wasted_bytes"]),
            "groups_preview": groups_preview,
        }
        return Report(
            report_type=REPORT_TYPE_DUPLICATE,
            title=f"Scan: {result['root_dir']}",
            summary=f"{result['duplicate_groups_count']} duplicate groups, "
                    f"{_human_size(result['wasted_bytes'])} wasted",
            data=data,
        )
