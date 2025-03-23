import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager
from src.utils.ui_helpers import (
    ButtonCursorHandler,
    DialogAutoSelectFilter,
    apply_auto_select_to_widget,
)
from src.utils.theme_manager import ThemeManager


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialiser le gestionnaire de curseurs pour les boutons
    button_cursor_handler = ButtonCursorHandler()

    # Initialiser le gestionnaire de sélection automatique pour les dialogues
    dialog_select_handler = DialogAutoSelectFilter()

    # Initialiser la base de données
    db_manager = DatabaseManager()
    db_manager.init_db()

    # Initialiser le gestionnaire de thèmes
    theme_manager = ThemeManager(db_manager)

    # Fonction pour appliquer un thème
    def apply_theme(theme_name):
        print(f"Application du thème : {theme_name}")
        # Mettre à jour le thème actuel
        theme_manager.current_theme_name = theme_name
        # Générer et appliquer le style
        qss = theme_manager.generate_stylesheet("src/ui/style/style_template.qss")
        app.setStyleSheet(qss)

    # Appliquer le thème initial en utilisant le thème stocké en base de données
    initial_theme = theme_manager.get_current_theme()
    apply_theme(initial_theme)

    # Créer et afficher la fenêtre principale
    window = MainWindow(db_manager)

    # Connecter le signal de changement de thème à notre fonction
    window.options_tab.theme_changed.connect(apply_theme)

    # Appliquer la sélection automatique à tous les champs de saisie
    apply_auto_select_to_widget(window)

    window.show()

    sys.exit(app.exec())
