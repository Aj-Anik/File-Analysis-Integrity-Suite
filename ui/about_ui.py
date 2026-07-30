"""
ui/about_ui.py

Module 5: About Section.

Static informational tab: project description, technologies used,
DSA concepts demonstrated, and developer information.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout


class AboutTab(QWidget):
    """Top-level widget for the About Section module."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel("About This Project")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        layout.addWidget(self._description_card())
        layout.addWidget(self._tech_card())
        layout.addWidget(self._dsa_card())
        layout.addWidget(self._developer_card())
        layout.addStretch()

    def _card(self, heading: str) -> tuple:
        frame = QFrame()
        frame.setObjectName("ContentCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        label = QLabel(heading)
        label.setObjectName("SectionLabel")
        layout.addWidget(label)
        return frame, layout

    def _description_card(self) -> QFrame:
        frame, layout = self._card("Project Description")
        text = QLabel(
            "Smart Academic Integrity &amp; File Optimization Suite is a desktop application "
            "that brings together four practical, real-world tools into one program: a "
            "plagiarism detector, a Huffman-coding file compressor, a duplicate file finder, "
            "and a history/reporting system. The project was built to demonstrate how "
            "classic Data Structures and Algorithms (DSA) concepts -- hash tables, heaps, "
            "binary trees, stacks, queues, sets, and string-matching algorithms -- map onto "
            "genuinely useful software, rather than staying confined to textbook exercises."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        return frame

    def _tech_card(self) -> QFrame:
        frame, layout = self._card("Technologies Used")
        items = [
            "Python 3.x - core application language",
            "PyQt6 - desktop GUI framework",
            "python-docx - reading .docx documents",
            "pypdf - reading and extracting text from PDF files",
            "reportlab - generating PDF reports",
            "hashlib (SHA-256) - file content hashing",
            "JSON - lightweight file-based persistence for history & reports",
        ]
        for item in items:
            lbl = QLabel(f"\u2022 {item}")
            layout.addWidget(lbl)
        return frame

    def _dsa_card(self) -> QFrame:
        frame, layout = self._card("DSA Concepts Demonstrated")
        grid = QGridLayout()
        items = [
            ("Arrays / Lists", "Tokenized word lists, file scan results, history records"),
            ("Hash Tables", "Term-frequency vectors, byte frequency tables, duplicate hash buckets"),
            ("Sets", "Jaccard similarity, common/unique keyword extraction"),
            ("Stacks", "Undo-last-delete in History & Reports"),
            ("Queues", "Recent Activity feed (bounded FIFO via collections.deque)"),
            ("Priority Queues (Heap)", "Building the Huffman coding tree with heapq"),
            ("Binary Trees", "The Huffman coding tree itself"),
            ("String Matching", "Rabin-Karp (rolling hash) and KMP (prefix function)"),
            ("Searching Algorithms", "Linear search, binary search, fuzzy substring search"),
            ("Sorting Algorithms", "Merge sort and quick sort (custom implementations)"),
        ]
        for i, (concept, usage) in enumerate(items):
            concept_lbl = QLabel(f"<b>{concept}</b>")
            usage_lbl = QLabel(usage)
            usage_lbl.setWordWrap(True)
            usage_lbl.setObjectName("StatCaption")
            grid.addWidget(concept_lbl, i, 0)
            grid.addWidget(usage_lbl, i, 1)
        layout.addLayout(grid)
        return frame

    def _developer_card(self) -> QFrame:
        frame, layout = self._card("Developer Information")
        text = QLabel(
            "<b>Kazi Abu Jafar Anik(C251015)</b> <br>" \
            "<b>Mashrafe Bin Hasnath(C251006)</b><br>" \
            "<b>Tanvir Rubayet(C251055)</b>"
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        return frame
