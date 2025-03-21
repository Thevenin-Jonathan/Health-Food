import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager
from src.utils.ui_helpers import apply_auto_select_to_widget
from src.utils.qss_preprocessor import process_qss


if __name__ == "__main__":
    app = QApplication(sys.argv)

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

    # Appliquer le curseur pointant à tous les boutons
    setup_cursor_for_buttons(window)

    window.showMaximized()

    sys.exit(app.exec())
