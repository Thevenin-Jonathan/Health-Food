import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager


class PointerCursorButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)


def setup_cursor_for_buttons(widget):
    """Applique le curseur pointant à tous les boutons dans le widget et ses enfants"""
    for child in widget.findChildren(QPushButton):
        child.setCursor(Qt.PointingHandCursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Appliquer un style global à l'application
    with open("src/ui/style/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    # Initialiser la base de données
    db_manager = DatabaseManager()
    db_manager.init_db()

    # Créer et afficher la fenêtre principale
    window = MainWindow(db_manager)

    # Appliquer le curseur pointant à tous les boutons
    setup_cursor_for_buttons(window)

    window.showMaximized()

    sys.exit(app.exec())
