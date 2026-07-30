"""
ui/theme.py

Centralized QSS (Qt Style Sheet) definitions for Dark Mode and Light Mode.
Keeping styling in one place lets main_window.py swap the entire app's
look with a single setStyleSheet() call.
"""

LIGHT_THEME = """
QWidget {
    background-color: #F4F6FB;
    color: #1E2233;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #F4F6FB;
}

#Sidebar {
    background-color: #1E2A78;
    border: none;
}

#SidebarTitle {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    padding: 18px 16px 4px 16px;
}

#SidebarSubtitle {
    color: #B7C0E8;
    font-size: 10.5px;
    padding: 0px 16px 18px 16px;
}

QPushButton#NavButton {
    background-color: transparent;
    color: #D7DCF5;
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-radius: 0px;
    font-size: 13.5px;
    font-weight: 500;
}

QPushButton#NavButton:hover {
    background-color: #2C3A93;
    color: #FFFFFF;
}

QPushButton#NavButton:checked {
    background-color: #3E50B4;
    color: #FFFFFF;
    border-left: 4px solid #7C9BFF;
    font-weight: 700;
}

QFrame#ContentCard {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E3E7F3;
}

QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: #1E2A78;
}

QLabel#PageSubtitle {
    font-size: 12.5px;
    color: #6B7290;
    margin-bottom: 8px;
}

QLabel#SectionLabel {
    font-size: 13px;
    font-weight: 600;
    color: #2E3A87;
}

QLabel#StatValue {
    font-size: 26px;
    font-weight: 800;
    color: #1E2A78;
}

QLabel#StatCaption {
    font-size: 11px;
    color: #6B7290;
}

QFrame#StatCard {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E3E7F3;
}

QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #DDE2F2;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #B7C0E8;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #3E50B4;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #DDE2F2;
    border-radius: 8px;
    padding: 7px 10px;
}

QLineEdit:focus {
    border: 1.5px solid #3E50B4;
}

QPushButton#PrimaryButton {
    background-color: #3E50B4;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #2E3A87;
}

QPushButton#PrimaryButton:disabled {
    background-color: #B6BEDD;
}

QPushButton#SecondaryButton {
    background-color: #EDEFFA;
    color: #2E3A87;
    border: 1.5px solid #C7CDF0;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton#SecondaryButton:hover {
    background-color: #DCE0F7;
}

QPushButton#DangerButton {
    background-color: #FBEAEA;
    color: #B23A3A;
    border: 1.5px solid #EFC4C4;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton#DangerButton:hover {
    background-color: #F7D6D6;
}

QProgressBar {
    background-color: #E9EBF6;
    border: none;
    border-radius: 6px;
    text-align: center;
    height: 16px;
    color: #1E2233;
    font-size: 10.5px;
}

QProgressBar::chunk {
    background-color: #3E50B4;
    border-radius: 6px;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E3E7F3;
    border-radius: 8px;
    gridline-color: #EEF0F9;
}

QHeaderView::section {
    background-color: #EDEFFA;
    color: #2E3A87;
    font-weight: 600;
    padding: 6px;
    border: none;
}

QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E3E7F3;
    border-radius: 8px;
}

QTabWidget::pane {
    border: 1px solid #E3E7F3;
    border-radius: 8px;
}

QTabBar::tab {
    background: #EDEFFA;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #2E3A87;
}

QTabBar::tab:selected {
    background: #3E50B4;
    color: white;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1.5px solid #DDE2F2;
    border-radius: 8px;
    padding: 6px 10px;
}

QScrollBar:vertical {
    background: #F4F6FB;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #C7CDF0;
    border-radius: 5px;
}
"""

DARK_THEME = """
QWidget {
    background-color: #161B2E;
    color: #E5E8F5;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #161B2E;
}

#Sidebar {
    background-color: #0E1224;
    border: none;
}

#SidebarTitle {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    padding: 18px 16px 4px 16px;
}

#SidebarSubtitle {
    color: #6E78A8;
    font-size: 10.5px;
    padding: 0px 16px 18px 16px;
}

QPushButton#NavButton {
    background-color: transparent;
    color: #AEB6DE;
    text-align: left;
    padding: 12px 18px;
    border: none;
    font-size: 13.5px;
    font-weight: 500;
}

QPushButton#NavButton:hover {
    background-color: #1C2347;
    color: #FFFFFF;
}

QPushButton#NavButton:checked {
    background-color: #2C3568;
    color: #FFFFFF;
    border-left: 4px solid #6E84FF;
    font-weight: 700;
}

QFrame#ContentCard {
    background-color: #1E2440;
    border-radius: 12px;
    border: 1px solid #2A3158;
}

QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#PageSubtitle {
    font-size: 12.5px;
    color: #8E97C4;
    margin-bottom: 8px;
}

QLabel#SectionLabel {
    font-size: 13px;
    font-weight: 600;
    color: #8FA0FF;
}

QLabel#StatValue {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
}

QLabel#StatCaption {
    font-size: 11px;
    color: #8E97C4;
}

QFrame#StatCard {
    background-color: #1E2440;
    border-radius: 10px;
    border: 1px solid #2A3158;
}

QTextEdit, QPlainTextEdit {
    background-color: #1E2440;
    color: #E5E8F5;
    border: 1.5px solid #2A3158;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #3E50B4;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #6E84FF;
}

QLineEdit {
    background-color: #1E2440;
    color: #E5E8F5;
    border: 1.5px solid #2A3158;
    border-radius: 8px;
    padding: 7px 10px;
}

QLineEdit:focus {
    border: 1.5px solid #6E84FF;
}

QPushButton#PrimaryButton {
    background-color: #5468E0;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #6577EE;
}

QPushButton#PrimaryButton:disabled {
    background-color: #3A4070;
}

QPushButton#SecondaryButton {
    background-color: #252C50;
    color: #AEB6DE;
    border: 1.5px solid #353D6E;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton#SecondaryButton:hover {
    background-color: #2F3766;
}

QPushButton#DangerButton {
    background-color: #3A2230;
    color: #F2A0A0;
    border: 1.5px solid #5A2E3D;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton#DangerButton:hover {
    background-color: #4A2A3A;
}

QProgressBar {
    background-color: #252C50;
    border: none;
    border-radius: 6px;
    text-align: center;
    height: 16px;
    color: #E5E8F5;
    font-size: 10.5px;
}

QProgressBar::chunk {
    background-color: #5468E0;
    border-radius: 6px;
}

QTableWidget {
    background-color: #1E2440;
    color: #E5E8F5;
    border: 1px solid #2A3158;
    border-radius: 8px;
    gridline-color: #2A3158;
}

QHeaderView::section {
    background-color: #252C50;
    color: #8FA0FF;
    font-weight: 600;
    padding: 6px;
    border: none;
}

QListWidget {
    background-color: #1E2440;
    color: #E5E8F5;
    border: 1px solid #2A3158;
    border-radius: 8px;
}

QTabWidget::pane {
    border: 1px solid #2A3158;
    border-radius: 8px;
}

QTabBar::tab {
    background: #252C50;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #AEB6DE;
}

QTabBar::tab:selected {
    background: #5468E0;
    color: white;
}

QComboBox {
    background-color: #1E2440;
    color: #E5E8F5;
    border: 1.5px solid #2A3158;
    border-radius: 8px;
    padding: 6px 10px;
}

QScrollBar:vertical {
    background: #161B2E;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #353D6E;
    border-radius: 5px;
}
"""


def get_theme(name: str) -> str:
    """Return the QSS string for 'light' or 'dark'. Defaults to light on unknown input."""
    return DARK_THEME if name == "dark" else LIGHT_THEME
