from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QButtonGroup, QFrame, QSizePolicy,
)

from models.history import HistoryManager
from ui.theme import get_theme
from ui.plagiarism_ui import PlagiarismTab
from ui.compression_ui import CompressionTab
from ui.duplicate_ui import DuplicateTab
from ui.history_ui import HistoryTab
from ui.about_ui import AboutTab


NAV_ITEMS = [
    ("Plagiarism Detector", "plagiarism"),
    ("File Compression", "compression"),
    ("Duplicate Finder", "duplicate"),
    ("History & Reports", "history"),
    ("About", "about"),
]


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Analysis & Integrity Suite")
        self.resize(1280, 820)
        self.setMinimumSize(980, 640)

        self.history_manager = HistoryManager()
        self.current_theme = "light"

        self._build_ui()
        self.apply_theme(self.current_theme)

    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        # Instantiate all five module tabs
        self.plagiarism_tab = PlagiarismTab()
        self.compression_tab = CompressionTab()
        self.duplicate_tab = DuplicateTab()
        self.history_tab = HistoryTab(self.history_manager)
        self.about_tab = AboutTab()

        self.stack.addWidget(self.plagiarism_tab)
        self.stack.addWidget(self.compression_tab)
        self.stack.addWidget(self.duplicate_tab)
        self.stack.addWidget(self.history_tab)
        self.stack.addWidget(self.about_tab)

        # Wire "Save to History" signals from each module into the shared HistoryManager
        self.plagiarism_tab.report_created.connect(self.history_tab.add_report)
        self.compression_tab.report_created.connect(self.history_tab.add_report)
        self.duplicate_tab.report_created.connect(self.history_tab.add_report)

        self.nav_buttons[0].setChecked(True)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Academic Integrity\n&& File Suite")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("DSA Desktop Application")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.nav_buttons = []
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)

        for i, (label, _key) in enumerate(NAV_ITEMS):
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda _checked, idx=i: self._on_nav_clicked(idx))
            self.nav_button_group.addButton(btn, i)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        theme_row = QHBoxLayout()
        theme_row.setContentsMargins(16, 10, 16, 16)
        self.theme_toggle_btn = QPushButton("Switch to Dark Mode")
        self.theme_toggle_btn.setObjectName("SecondaryButton")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        theme_row.addWidget(self.theme_toggle_btn)
        layout.addLayout(theme_row)

        return sidebar

    # ------------------------------------------------------------------ #
    def _on_nav_clicked(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 3:  
            self.history_tab.refresh()

    def toggle_theme(self) -> None:
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(self.current_theme)

    def apply_theme(self, theme_name: str) -> None:
        self.setStyleSheet(get_theme(theme_name))
        self.theme_toggle_btn.setText(
            "Switch to Dark Mode" if theme_name == "light" else "Switch to Light Mode"
        )
