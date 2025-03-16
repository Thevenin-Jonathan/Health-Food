import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager

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
    window.show()

    sys.exit(app.exec())
