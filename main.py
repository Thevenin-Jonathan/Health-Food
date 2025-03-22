import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager
from src.utils.ui_helpers import ButtonCursorHandler, apply_auto_select_to_widget
from src.utils.qss_preprocessor import process_qss


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialiser le gestionnaire de curseurs pour les boutons
    button_cursor_handler = ButtonCursorHandler()

    # Générer le QSS à partir du template en utilisant le préprocesseur
    qss_content = process_qss(
        "src/ui/style/style_template.qss",
        "src/ui/style/style_generated.qss",  # Crée un fichier généré (optionnel)
    )

    # Appliquer le style généré
    app.setStyleSheet(qss_content)

    # Initialiser la base de données
    db_manager = DatabaseManager()
    db_manager.init_db()

    # Créer et afficher la fenêtre principale
    window = MainWindow(db_manager)

    # Appliquer la sélection automatique à tous les champs de saisie
    apply_auto_select_to_widget(window)

    # window.showMaximized()
    window.show()

    sys.exit(app.exec())
