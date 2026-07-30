"""
main.py

Entry point for the Smart Academic Integrity & File Optimization Suite.

Run with:
    python main.py

Requires PyQt6 and the other packages listed in requirements.txt to be
installed first:
    pip install -r requirements.txt
"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Academic Integrity & File Optimization Suite")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
