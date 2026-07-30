"""
ui/plagiarism_ui.py

Module 1: Plagiarism Detector tab.

Provides:
    * Two large text boxes (manual entry) OR file upload (.txt/.docx/.pdf)
      for each side of the comparison.
    * Drag-and-drop support via DropZoneLabel.
    * A background QThread worker so the UI never freezes while comparing
      (a progress bar animates during analysis).
    * A results panel: similarity gauge, Jaccard/Cosine breakdown, common
      and unique keywords, matching phrases, word counts, elapsed time.
    * "Export as PDF" and "Save to History" actions.
"""

import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QFrame, QProgressBar, QMessageBox, QScrollArea,
    QTabWidget, QSizePolicy,
)

from algorithms.plagiarism import compare_texts, compare_files, read_any_supported_file, UnsupportedFileTypeError
from algorithms.pdf_export import export_plagiarism_report
from models.report import Report, REPORT_TYPE_PLAGIARISM
from ui.widgets import DropZoneLabel, SimilarityGauge
from utils.paths import ensure_reports_dir


class PlagiarismWorker(QThread):
    """
    Runs the (potentially slow, for large documents) text comparison off
    the main GUI thread so the interface stays responsive.
    """
    finished = pyqtSignal(object)   # emits a PlagiarismResult
    failed = pyqtSignal(str)

    def __init__(self, text_a: str, text_b: str, label_a: str, label_b: str):
        super().__init__()
        self.text_a = text_a
        self.text_b = text_b
        self.label_a = label_a
        self.label_b = label_b

    def run(self) -> None:
        try:
            result = compare_texts(self.text_a, self.text_b, self.label_a, self.label_b)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - surface any error to the UI
            self.failed.emit(str(exc))


class PlagiarismTab(QWidget):
    """Top-level widget for the Plagiarism Detector module."""

    report_created = pyqtSignal(object)  # emits a Report, picked up by MainWindow -> HistoryManager

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_path_a = None
        self.loaded_path_b = None
        self.last_result = None
        self.worker = None
        self._build_ui()

    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel("Plagiarism Detector")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Compare two documents and calculate a similarity score using "
                           "Jaccard, Cosine, and Rabin-Karp/KMP phrase matching.")
        subtitle.setObjectName("PageSubtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        # Scrollable area so results don't squeeze the input area on small screens
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

        input_tabs = QTabWidget()
        input_tabs.addTab(self._build_manual_entry_tab(), "Manual Text Entry")
        input_tabs.addTab(self._build_file_upload_tab(), "Upload Files")
        input_layout.addWidget(input_tabs)

        action_row = QHBoxLayout()
        self.compare_btn = QPushButton("Compare Texts")
        self.compare_btn.setObjectName("PrimaryButton")
        self.compare_btn.clicked.connect(self.on_compare_clicked)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setObjectName("SecondaryButton")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        action_row.addWidget(self.compare_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addStretch()
        input_layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate (busy) until result arrives
        self.progress_bar.setVisible(False)
        input_layout.addWidget(self.progress_bar)

        scroll_layout.addWidget(input_card)

        # --- Results card ---
        self.results_card = QFrame()
        self.results_card.setObjectName("ContentCard")
        self.results_card.setVisible(False)
        self._build_results_section()
        scroll_layout.addWidget(self.results_card)
        scroll_layout.addStretch()

    def _build_manual_entry_tab(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(10)

        label_a = QLabel("Text A")
        label_a.setObjectName("SectionLabel")
        self.text_box_a = QTextEdit()
        self.text_box_a.setPlaceholderText("Paste or type the first document here...")
        self.text_box_a.setMinimumHeight(160)

        label_b = QLabel("Text B")
        label_b.setObjectName("SectionLabel")
        self.text_box_b = QTextEdit()
        self.text_box_b.setPlaceholderText("Paste or type the second document here...")
        self.text_box_b.setMinimumHeight(160)

        layout.addWidget(label_a, 0, 0)
        layout.addWidget(label_b, 0, 1)
        layout.addWidget(self.text_box_a, 1, 0)
        layout.addWidget(self.text_box_b, 1, 1)
        return widget

    def _build_file_upload_tab(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(10)

        allowed = [".txt", ".docx", ".pdf"]

        label_a = QLabel("Document A (.txt, .docx, .pdf)")
        label_a.setObjectName("SectionLabel")
        self.drop_a = DropZoneLabel("Drag & drop a file here\nor click 'Browse' below", allowed)
        self.drop_a.file_dropped.connect(lambda path: self._on_file_chosen("a", path))
        browse_a = QPushButton("Browse for Document A...")
        browse_a.setObjectName("SecondaryButton")
        browse_a.clicked.connect(lambda: self._browse_file("a"))

        label_b = QLabel("Document B (.txt, .docx, .pdf)")
        label_b.setObjectName("SectionLabel")
        self.drop_b = DropZoneLabel("Drag & drop a file here\nor click 'Browse' below", allowed)
        self.drop_b.file_dropped.connect(lambda path: self._on_file_chosen("b", path))
        browse_b = QPushButton("Browse for Document B...")
        browse_b.setObjectName("SecondaryButton")
        browse_b.clicked.connect(lambda: self._browse_file("b"))

        layout.addWidget(label_a, 0, 0)
        layout.addWidget(label_b, 0, 1)
        layout.addWidget(self.drop_a, 1, 0)
        layout.addWidget(self.drop_b, 1, 1)
        layout.addWidget(browse_a, 2, 0)
        layout.addWidget(browse_b, 2, 1)
        return widget

    def _build_results_section(self) -> None:
        layout = QVBoxLayout(self.results_card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        results_title = QLabel("Comparison Results")
        results_title.setObjectName("SectionLabel")
        header_row.addWidget(results_title)
        header_row.addStretch()
        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.setObjectName("SecondaryButton")
        self.export_pdf_btn.clicked.connect(self.on_export_pdf)
        self.save_history_btn = QPushButton("Save to History")
        self.save_history_btn.setObjectName("PrimaryButton")
        self.save_history_btn.clicked.connect(self.on_save_to_history)
        header_row.addWidget(self.export_pdf_btn)
        header_row.addWidget(self.save_history_btn)
        layout.addLayout(header_row)

        top_row = QHBoxLayout()
        self.gauge = SimilarityGauge()
        top_row.addWidget(self.gauge)

        metrics_layout = QGridLayout()
        self.jaccard_label = QLabel("Jaccard Similarity: -")
        self.cosine_label = QLabel("Cosine Similarity: -")
        self.match_count_label = QLabel("Matching Words: -")
        self.wordcount_label = QLabel("Word Counts: -")
        self.time_label = QLabel("Time Taken: -")
        for lbl in (self.jaccard_label, self.cosine_label, self.match_count_label,
                    self.wordcount_label, self.time_label):
            lbl.setWordWrap(True)
        metrics_layout.addWidget(self.jaccard_label, 0, 0)
        metrics_layout.addWidget(self.cosine_label, 1, 0)
        metrics_layout.addWidget(self.match_count_label, 2, 0)
        metrics_layout.addWidget(self.wordcount_label, 3, 0)
        metrics_layout.addWidget(self.time_label, 4, 0)
        top_row.addLayout(metrics_layout, 1)
        layout.addLayout(top_row)

        # Detailed tabs: common words / unique A / unique B / matching phrases
        self.detail_tabs = QTabWidget()
        self.common_words_box = QTextEdit()
        self.common_words_box.setReadOnly(True)
        self.unique_a_box = QTextEdit()
        self.unique_a_box.setReadOnly(True)
        self.unique_b_box = QTextEdit()
        self.unique_b_box.setReadOnly(True)
        self.phrases_box = QTextEdit()
        self.phrases_box.setReadOnly(True)

        self.detail_tabs.addTab(self.common_words_box, "Common Keywords")
        self.detail_tabs.addTab(self.unique_a_box, "Unique to A")
        self.detail_tabs.addTab(self.unique_b_box, "Unique to B")
        self.detail_tabs.addTab(self.phrases_box, "Matching Phrases")
        layout.addWidget(self.detail_tabs)

    # ------------------------------------------------------------------ #
    # File handling
    # ------------------------------------------------------------------ #
    def _browse_file(self, side: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select Document {side.upper()}", "",
            "Supported Documents (*.txt *.docx *.pdf);;All Files (*)",
        )
        if path:
            self._on_file_chosen(side, path)

    def _on_file_chosen(self, side: str, path: str) -> None:
        if side == "a":
            self.loaded_path_a = path
            self.drop_a.setText(f"Selected:\n{os.path.basename(path)}")
        else:
            self.loaded_path_b = path
            self.drop_b.setText(f"Selected:\n{os.path.basename(path)}")

    # ------------------------------------------------------------------ #
    # Compare action
    # ------------------------------------------------------------------ #
    def on_compare_clicked(self) -> None:
        text_a, text_b, label_a, label_b = "", "", "Text A", "Text B"

        # Prefer manual text if either box has content typed in; otherwise fall back to uploaded files.
        manual_a = self.text_box_a.toPlainText().strip()
        manual_b = self.text_box_b.toPlainText().strip()

        try:
            if manual_a or manual_b:
                text_a, text_b = manual_a, manual_b
            elif self.loaded_path_a and self.loaded_path_b:
                text_a = read_any_supported_file(self.loaded_path_a)
                text_b = read_any_supported_file(self.loaded_path_b)
                label_a = os.path.basename(self.loaded_path_a)
                label_b = os.path.basename(self.loaded_path_b)
            else:
                QMessageBox.warning(
                    self, "Missing Input",
                    "Please enter text in both boxes, or upload both Document A and Document B.",
                )
                return
        except UnsupportedFileTypeError as e:
            QMessageBox.critical(self, "Unsupported File", str(e))
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error Reading File", f"Could not read the selected file:\n{e}")
            return

        if not text_a.strip() or not text_b.strip():
            QMessageBox.warning(self, "Empty Input", "Both Text A and Text B must contain some content.")
            return

        self.compare_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = PlagiarismWorker(text_a, text_b, label_a, label_b)
        self.worker.finished.connect(self._on_compare_finished)
        self.worker.failed.connect(self._on_compare_failed)
        self.worker.start()

    def _on_compare_finished(self, result) -> None:
        self.progress_bar.setVisible(False)
        self.compare_btn.setEnabled(True)
        self.last_result = result
        self.results_card.setVisible(True)

        self.gauge.set_value(result.overall_similarity_percent)
        self.jaccard_label.setText(f"<b>Jaccard Similarity:</b> {round(result.jaccard_score * 100, 2)}%")
        self.cosine_label.setText(f"<b>Cosine Similarity:</b> {round(result.cosine_score * 100, 2)}%")
        self.match_count_label.setText(f"<b>Matching Words:</b> {result.matching_word_count}")
        self.wordcount_label.setText(
            f"<b>Word Counts:</b> {result.label_a} = {result.word_count_a}, "
            f"{result.label_b} = {result.word_count_b}"
        )
        self.time_label.setText(f"<b>Time Taken:</b> {result.time_taken_seconds} seconds")

        self.common_words_box.setPlainText(", ".join(result.common_words) or "No common words found.")
        self.unique_a_box.setPlainText(", ".join(result.unique_to_a) or "None.")
        self.unique_b_box.setPlainText(", ".join(result.unique_to_b) or "None.")
        self.phrases_box.setPlainText(
            "\n".join(f"\u2022 {p}" for p in result.matching_phrases)
            or "No contiguous matching phrases of 5+ words were detected."
        )

    def _on_compare_failed(self, error_msg: str) -> None:
        self.progress_bar.setVisible(False)
        self.compare_btn.setEnabled(True)
        QMessageBox.critical(self, "Comparison Failed", f"An error occurred during analysis:\n{error_msg}")

    def on_clear_clicked(self) -> None:
        self.text_box_a.clear()
        self.text_box_b.clear()
        self.drop_a.reset_text()
        self.drop_b.reset_text()
        self.loaded_path_a = None
        self.loaded_path_b = None
        self.results_card.setVisible(False)
        self.last_result = None

    # ------------------------------------------------------------------ #
    # Export / Save
    # ------------------------------------------------------------------ #
    def on_export_pdf(self) -> None:
        if not self.last_result:
            return
        default_path = os.path.join(ensure_reports_dir(), "plagiarism_report.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        try:
            report = Report(
                report_type=REPORT_TYPE_PLAGIARISM,
                title=f"{self.last_result.label_a} vs {self.last_result.label_b}",
                summary=f"{self.last_result.overall_similarity_percent}% similarity",
                data=self.last_result.to_dict(),
            )
            export_plagiarism_report(report, path)
            QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF:\n{e}")

    def on_save_to_history(self) -> None:
        if not self.last_result:
            return
        report = Report(
            report_type=REPORT_TYPE_PLAGIARISM,
            title=f"{self.last_result.label_a} vs {self.last_result.label_b}",
            summary=f"{self.last_result.overall_similarity_percent}% similarity",
            data=self.last_result.to_dict(),
        )
        self.report_created.emit(report)
        QMessageBox.information(self, "Saved", "This comparison has been saved to History & Reports.")
