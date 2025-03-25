import sys
from PySide6.QtWidgets import QApplication, QMessageBox
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

    try:
        # Initialiser le gestionnaire de curseurs pour les boutons
        button_cursor_handler = ButtonCursorHandler()

        # Initialiser le gestionnaire de sélection automatique pour les dialogues
        dialog_select_handler = DialogAutoSelectFilter()

        # Initialiser la base de données avec gestion d'erreur
        print("Initialisation de la base de données...")
        db_manager = DatabaseManager()
        db_manager.init_db()

        # Initialiser le gestionnaire de thèmes
        theme_manager = ThemeManager(db_manager)

        # Fonction pour appliquer un thème
        def apply_theme(theme_name):
            # Mettre à jour le thème actuel
            theme_manager.current_theme_name = theme_name
            # Générer et appliquer le style
            qss = theme_manager.generate_stylesheet("src/ui/style/style_template.qss")
            app.setStyleSheet(qss)

        # Appliquer le thème initial en utilisant le thème stocké en base de données
        try:
            INITIAL_THEME = theme_manager.get_current_theme()
            if not INITIAL_THEME:
                INITIAL_THEME = "Vert Nature"  # Thème par défaut
            apply_theme(INITIAL_THEME)
        except Exception as e:
            print(f"Erreur lors de l'application du thème initial: {e}")
            apply_theme("Vert Nature")  # Fallback au thème par défaut

        # Créer et afficher la fenêtre principale
        window = MainWindow(db_manager)

        # Connecter le signal de changement de thème à notre fonction
        window.options_tab.theme_changed.connect(apply_theme)

        # Appliquer la sélection automatique à tous les champs de saisie
        apply_auto_select_to_widget(window)

        window.show()

        sys.exit(app.exec())
    except Exception as e:
        print(f"Erreur critique au démarrage de l'application: {e}")
        from traceback import print_exc

        print_exc()

        # Afficher un message d'erreur à l'utilisateur
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Erreur au démarrage")
        error_box.setText(
            "Une erreur critique est survenue au démarrage de l'application."
        )
        error_box.setDetailedText(str(e))
        error_box.exec()
        sys.exit(1)
