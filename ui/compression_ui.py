"""
ui/compression_ui.py

Module 2: File Compression & Decompression tab.

Lets the user select any file (drag-and-drop or browse), compress it with
Huffman coding into a custom .huf container, or decompress an existing
.huf file back to its original form. Displays frequency table, Huffman
code table, and compression statistics.
"""

import os

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QProgressBar, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea,
)

from algorithms.huffman import compress_file, decompress_file, CorruptHuffmanFileError
from algorithms.pdf_export import export_compression_report
from models.report import Report, REPORT_TYPE_COMPRESSION
from ui.widgets import DropZoneLabel, StatCard
from utils.paths import ensure_reports_dir


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def _printable_byte(byte_value: int) -> str:
    if 32 <= byte_value < 127:
        return f"'{chr(byte_value)}'"
    return f"0x{byte_value:02X}"


class CompressWorker(QThread):
    finished = pyqtSignal(dict, str)  # stats, output_path
    failed = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        try:
            stats = compress_file(self.input_path, self.output_path)
            self.finished.emit(stats, self.output_path)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class DecompressWorker(QThread):
    finished = pyqtSignal(int, str)  # bytes_written, output_path
    failed = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        try:
            n = decompress_file(self.input_path, self.output_path)
            self.finished.emit(n, self.output_path)
        except CorruptHuffmanFileError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class CompressionTab(QWidget):
    """Top-level widget for the File Compression & Decompression module."""

    report_created = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_path = None
        self.last_stats = None
        self.last_output_path = None
        self.worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel("File Compression & Decompression")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Compress any file using Huffman Coding, or restore a previously "
                           "compressed .huf file back to its original form.")
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

        self.drop_zone = DropZoneLabel("Drag & drop any file here\n(to compress, or a .huf file to decompress)")
        self.drop_zone.file_dropped.connect(self._on_file_chosen)
        input_layout.addWidget(self.drop_zone)

        browse_btn = QPushButton("Browse for a File...")
        browse_btn.setObjectName("SecondaryButton")
        browse_btn.clicked.connect(self._browse_file)
        input_layout.addWidget(browse_btn)

        action_row = QHBoxLayout()
        self.compress_btn = QPushButton("Compress File")
        self.compress_btn.setObjectName("PrimaryButton")
        self.compress_btn.clicked.connect(self.on_compress_clicked)
        self.decompress_btn = QPushButton("Decompress File")
        self.decompress_btn.setObjectName("SecondaryButton")
        self.decompress_btn.clicked.connect(self.on_decompress_clicked)
        action_row.addWidget(self.compress_btn)
        action_row.addWidget(self.decompress_btn)
        action_row.addStretch()
        input_layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
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

    def _build_results_section(self) -> None:
        layout = QVBoxLayout(self.results_card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        results_title = QLabel("Compression Results")
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

        stats_row = QHBoxLayout()
        self.original_card = StatCard("Original Size", "-")
        self.compressed_card = StatCard("Compressed Size", "-")
        self.ratio_card = StatCard("Compression Ratio", "-")
        self.saved_card = StatCard("Space Saved", "-")
        for card in (self.original_card, self.compressed_card, self.ratio_card, self.saved_card):
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        self.output_path_label = QLabel("")
        self.output_path_label.setWordWrap(True)
        layout.addWidget(self.output_path_label)

        table_label = QLabel("Frequency & Huffman Code Table")
        table_label.setObjectName("SectionLabel")
        layout.addWidget(table_label)

        self.code_table_widget = QTableWidget(0, 3)
        self.code_table_widget.setHorizontalHeaderLabels(["Byte", "Frequency", "Huffman Code"])
        self.code_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.code_table_widget.setMaximumHeight(260)
        layout.addWidget(self.code_table_widget)

    # ------------------------------------------------------------------ #
    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", "All Files (*)")
        if path:
            self._on_file_chosen(path)

    def _on_file_chosen(self, path: str) -> None:
        self.selected_path = path
        self.drop_zone.setText(f"Selected:\n{path}")

    def _set_busy(self, busy: bool) -> None:
        self.compress_btn.setEnabled(not busy)
        self.decompress_btn.setEnabled(not busy)
        self.progress_bar.setVisible(busy)

    # ------------------------------------------------------------------ #
    def on_compress_clicked(self) -> None:
        if not self.selected_path:
            QMessageBox.warning(self, "No File Selected", "Please choose a file to compress first.")
            return
        default_name = os.path.basename(self.selected_path) + ".huf"
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Compressed File", default_name, "Huffman Files (*.huf)")
        if not output_path:
            return

        self._set_busy(True)
        self.worker = CompressWorker(self.selected_path, output_path)
        self.worker.finished.connect(self._on_compress_finished)
        self.worker.failed.connect(self._on_operation_failed)
        self.worker.start()

    def _on_compress_finished(self, stats: dict, output_path: str) -> None:
        self._set_busy(False)
        self.last_stats = stats
        self.last_output_path = output_path
        self.results_card.setVisible(True)

        self.original_card.set_value(_human_size(stats["original_size"]))
        self.compressed_card.set_value(_human_size(stats["compressed_size"]))
        self.ratio_card.set_value(str(stats["compression_ratio"]))
        self.saved_card.set_value(f"{stats['space_saved_percent']}%")
        self.output_path_label.setText(f"<b>Saved to:</b> {output_path}")

        freq_table = stats.get("frequency_table", {})
        code_table = stats.get("code_table", {})
        sorted_bytes = sorted(freq_table.keys(), key=lambda b: -freq_table[b])

        self.code_table_widget.setRowCount(len(sorted_bytes))
        for row, byte_val in enumerate(sorted_bytes):
            self.code_table_widget.setItem(row, 0, QTableWidgetItem(_printable_byte(byte_val)))
            self.code_table_widget.setItem(row, 1, QTableWidgetItem(str(freq_table[byte_val])))
            self.code_table_widget.setItem(row, 2, QTableWidgetItem(code_table.get(byte_val, "")))

        QMessageBox.information(self, "Compression Complete",
                                 f"File compressed successfully.\nSpace saved: {stats['space_saved_percent']}%")

    def on_decompress_clicked(self) -> None:
        if not self.selected_path:
            QMessageBox.warning(self, "No File Selected", "Please choose a .huf file to decompress first.")
            return
        if not self.selected_path.lower().endswith(".huf"):
            reply = QMessageBox.question(
                self, "Confirm Decompression",
                "The selected file doesn't have a .huf extension. Try to decompress it anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        default_name = os.path.basename(self.selected_path).replace(".huf", "") + ".decompressed"
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Decompressed File", default_name, "All Files (*)")
        if not output_path:
            return

        self._set_busy(True)
        self.worker = DecompressWorker(self.selected_path, output_path)
        self.worker.finished.connect(self._on_decompress_finished)
        self.worker.failed.connect(self._on_operation_failed)
        self.worker.start()

    def _on_decompress_finished(self, n_bytes: int, output_path: str) -> None:
        self._set_busy(False)
        QMessageBox.information(
            self, "Decompression Complete",
            f"File restored successfully ({_human_size(n_bytes)}).\nSaved to:\n{output_path}",
        )

    def _on_operation_failed(self, error_msg: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, "Operation Failed", error_msg)

    # ------------------------------------------------------------------ #
    def on_export_pdf(self) -> None:
        if not self.last_stats:
            return
        default_path = os.path.join(ensure_reports_dir(), "compression_report.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", default_path, "PDF Files (*.pdf)")
        if not path:
            return
        report = self._build_report()
        try:
            export_compression_report(report, path)
            QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF:\n{e}")

    def on_save_to_history(self) -> None:
        if not self.last_stats:
            return
        report = self._build_report()
        self.report_created.emit(report)
        QMessageBox.information(self, "Saved", "This compression result has been saved to History & Reports.")

    def _build_report(self) -> Report:
        stats = self.last_stats
        freq_table = stats.get("frequency_table", {})
        code_table = stats.get("code_table", {})
        sorted_bytes = sorted(freq_table.keys(), key=lambda b: -freq_table[b])[:25]
        code_preview = [
            [_printable_byte(b), str(freq_table[b]), code_table.get(b, "")] for b in sorted_bytes
        ]
        data = {
            "filename": os.path.basename(self.selected_path) if self.selected_path else "-",
            "original_size": stats["original_size"],
            "compressed_size": stats["compressed_size"],
            "compression_ratio": stats["compression_ratio"],
            "space_saved_percent": stats["space_saved_percent"],
            "distinct_symbols": len(freq_table),
            "code_table_preview": code_preview,
        }
        return Report(
            report_type=REPORT_TYPE_COMPRESSION,
            title=os.path.basename(self.selected_path) if self.selected_path else "Compression Job",
            summary=f"{stats['space_saved_percent']}% space saved",
            data=data,
        )
