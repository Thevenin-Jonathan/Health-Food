import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from src.utils.updater import UpdateManager
from src.utils.app_info import APP_VERSION
from src.ui.main_window import MainWindow
from src.database.db_manager import DatabaseManager
from src.utils.theme_manager import ThemeManager
from src.ui.dialogs.update_dialog import UpdateDialog, UpdateReadyDialog
from src.utils.ui_helpers import (
    ButtonCursorHandler,
    DialogAutoSelectFilter,
    apply_auto_select_to_widget,
)


def resource_path(relative_path):
    """Obtient le chemin absolu vers une ressource, compatible dev/PyInstaller"""
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
            qss_path = resource_path("src/ui/style/style_template.qss")
            qss = theme_manager.generate_stylesheet(qss_path)
            app.setStyleSheet(qss)

        # Appliquer le thème initial en utilisant le thème stocké en base de données
        try:
            INITIAL_THEME = theme_manager.get_current_theme()
            if not INITIAL_THEME:
                INITIAL_THEME = "Vert Nature"  # Thème par défaut
            apply_theme(INITIAL_THEME)
        except (
            FileNotFoundError,
            ValueError,
            RuntimeError,
        ) as e:
            print(f"Erreur lors de l'application du thème initial: {e}")
            apply_theme("Vert Nature")  # Fallback au thème par défaut

        # Initialiser le gestionnaire de mises à jour
        update_manager = UpdateManager(app_version=APP_VERSION)

        # Fonction pour gérer les mises à jour disponibles
        def handle_update_available(update_info):
            # Ajouter la version actuelle aux informations
            update_info["current_version"] = APP_VERSION

            # Créer et afficher le dialogue de mise à jour
            update_dialog = UpdateDialog(update_info)

            # Connecter les signaux
            update_dialog.download_requested.connect(
                lambda: start_download(update_info, update_dialog)
            )

            # Afficher le dialogue
            update_dialog.exec()

        # Fonction pour démarrer le téléchargement
        def start_download(update_info, update_dialog):
            # Configurer la progression du téléchargement
            def update_progress(progress):
                update_dialog.set_progress(progress)

            # Connecter temporairement le signal de progression
            update_manager.update_progress.connect(update_progress)

            # Lancer le téléchargement
            installer_path = update_manager.download_update(update_info)

            # Déconnecter le signal de progression
            update_manager.update_progress.disconnect(update_progress)

            if installer_path:
                # Mettre à jour l'interface pour montrer que le téléchargement est terminé
                update_dialog.set_downloading(False)
                update_dialog.close()

                # Afficher la boîte de dialogue d'installation
                ready_dialog = UpdateReadyDialog()
                ready_dialog.install_requested.connect(
                    lambda: update_manager.install_update(installer_path)
                )
                ready_dialog.exec()

        # Connecter les signaux du gestionnaire de mises à jour
        update_manager.update_available.connect(handle_update_available)
        update_manager.update_error.connect(
            lambda msg: QMessageBox.warning(None, "Erreur de mise à jour", msg)
        )

        # Créer et afficher la fenêtre principale
        window = MainWindow(db_manager)

        # Connecter le signal de changement de thème à notre fonction
        window.options_tab.theme_changed.connect(apply_theme)

        # Appliquer la sélection automatique à tous les champs de saisie
        apply_auto_select_to_widget(window)

        # Mettre à jour l'onglet Options pour utiliser le gestionnaire de mises à jour
        window.options_tab.set_update_manager(update_manager)

        # Vérifier les mises à jour au démarrage (silencieusement) après un court délai
        QTimer.singleShot(3000, update_manager.check_for_updates)

        window.show()

        sys.exit(app.exec())
    except (FileNotFoundError, ValueError, RuntimeError) as e:
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
