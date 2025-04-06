import os
import shutil
import datetime
import traceback
import time
import gc
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QWidget,
    QComboBox,
    QFormLayout,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QLineEdit,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from src.utils.app_restart import restart_application
from src.utils.theme_manager import ThemeManager
from src.database.db_connector import DBConnector
from src.ui.dialogs.export_import_dialog import ExportImportDialog
from src.ui.dialogs.backup_select_dialog import BackupSelectDialog
from .tab_base import TabBase


class ResetDBConfirmDialog(QDialog):
    """Dialogue de confirmation pour la réinitialisation de la base de données"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmer la réinitialisation")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Message d'avertissement
        message = QLabel(
            "<b>Attention :</b> Vous êtes sur le point de réinitialiser la base de données. "
            "Cette action supprimera <b>définitivement</b> toutes vos données : "
            "aliments personnalisés, repas, plannings, recettes, etc."
        )
        message.setWordWrap(True)
        message.setStyleSheet("color: #cc0000;")
        layout.addWidget(message)

        # Option pour sauvegarder avant réinitialisation
        self.backup_checkbox = QCheckBox(
            "Créer une sauvegarde avant la réinitialisation"
        )
        self.backup_checkbox.setChecked(True)
        layout.addWidget(self.backup_checkbox)

        # Texte de confirmation à taper
        layout.addSpacing(10)
        layout.addWidget(QLabel('Pour confirmer, tapez "RESET" ci-dessous :'))

        self.confirm_input = QLineEdit()
        layout.addWidget(self.confirm_input)

        # Boutons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.button(QDialogButtonBox.Ok).setText("Réinitialiser")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Cancel).setText("Annuler")
        self.button_box.button(QDialogButtonBox.Cancel).setObjectName("cancelButton")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Connecter le signal de changement de texte
        self.confirm_input.textChanged.connect(self.validate_input)

    def validate_input(self, text):
        """Valide que l'utilisateur a bien tapé le texte de confirmation"""
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(text == "RESET")


class OptionsTab(TabBase):
    """Onglet des options de l'application"""

    theme_changed = Signal(str)

    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.theme_manager = ThemeManager(db_manager)
        self.setup_ui()

    def setup_ui(self):
        # Créer un layout principal sans marges pour le widget entier
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Créer un layout horizontal pour centrer le contenu
        center_layout = QHBoxLayout()

        # Créer un widget contenant le contenu réel avec sa largeur limitée
        content_widget = QWidget()
        content_widget.setMaximumWidth(900)
        content_widget.setMinimumWidth(700)

        # Layout principal du contenu
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        title = QLabel("<h1>Options</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Groupe pour les thèmes
        themes_group = QGroupBox("Personnalisation de l'interface :")
        themes_group.setProperty("class", "options-group")
        themes_layout = QVBoxLayout(themes_group)

        # Description
        themes_description = QLabel(
            "Choisissez un thème pour personnaliser l'apparence de l'application."
        )
        themes_description.setWordWrap(True)
        themes_description.setProperty("class", "export-import-description")
        themes_layout.addWidget(themes_description)

        # Formulaire pour la sélection de thème
        form_layout = QFormLayout()

        # Combobox pour sélectionner le thème
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_available_themes())

        # Sélectionner le thème actuel
        current_theme = self.theme_manager.get_current_theme()
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        # Connecter le signal de changement
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)

        form_layout.addRow("Thème :", self.theme_combo)
        themes_layout.addLayout(form_layout)

        # Ajouter le groupe de thèmes
        main_layout.addWidget(themes_group)

        # Groupe pour l'exportation/importation
        export_import_group = QGroupBox("Exportation et Importation des données :")
        export_import_group.setProperty("class", "options-group")
        export_import_layout = QVBoxLayout(export_import_group)

        # Description
        description = QLabel(
            "Exportez vos aliments, recettes et plannings pour les sauvegarder ou les partager. "
            "Vous pouvez également importer des données préalablement exportées."
        )
        description.setWordWrap(True)
        description.setProperty("class", "export-import-description")
        export_import_layout.addWidget(description)

        # Bouton d'exportation/importation
        export_import_btn = QPushButton(
            "Ouvrir la fenêtre d'exportation/importation..."
        )
        export_import_btn.setObjectName("primaryButton")
        export_import_btn.clicked.connect(self.show_export_import_dialog)
        export_import_layout.addWidget(export_import_btn, 0, Qt.AlignCenter)

        main_layout.addWidget(export_import_group)

        # NOUVELLE SECTION: Groupe pour la réinitialisation de la base de données
        reset_db_group = QGroupBox("Gestion de la base de données :")
        reset_db_group.setProperty("class", "options-group")
        reset_db_layout = QVBoxLayout(reset_db_group)

        # Description
        reset_description = QLabel(
            "Ces options vous permettent de gérer votre base de données. La réinitialisation supprimera toutes vos "
            "données personnelles et restaurera les valeurs par défaut. La restauration vous permet de revenir "
            "à une sauvegarde précédente."
        )
        reset_description.setWordWrap(True)
        reset_description.setProperty("class", "reset-db-description")
        reset_db_layout.addWidget(reset_description)

        # Conteneur pour les boutons (layout horizontal)
        db_buttons_layout = QHBoxLayout()

        # Bouton de restauration
        restore_db_btn = QPushButton("Restaurer une sauvegarde...")
        restore_db_btn.clicked.connect(self.restore_database)
        db_buttons_layout.addWidget(restore_db_btn)

        # Séparateur visuel
        db_buttons_layout.addSpacing(20)

        # Nouveau bouton de sauvegarde au milieu
        create_backup_btn = QPushButton("Créer une sauvegarde...")
        create_backup_btn.clicked.connect(self.create_backup)
        db_buttons_layout.addWidget(create_backup_btn)

        # Séparateur visuel
        db_buttons_layout.addSpacing(20)

        # Bouton de réinitialisation avec style d'alerte
        reset_db_btn = QPushButton("Réinitialiser la base de données...")
        reset_db_btn.setObjectName("cancelButton")
        reset_db_btn.clicked.connect(self.reset_database)
        db_buttons_layout.addWidget(reset_db_btn)

        # Ajouter le layout des boutons au layout du groupe
        reset_db_layout.addLayout(db_buttons_layout)

        main_layout.addWidget(reset_db_group)

        # Ajouter un espace extensible en bas
        main_layout.addStretch()

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

    def on_theme_changed(self, theme_name):
        """Appelé lorsque l'utilisateur change de thème"""
        print(f"Thème sélectionné: {theme_name}")

        # Mettre à jour le thème actuel dans le gestionnaire de thèmes
        self.theme_manager.current_theme_name = theme_name

        # Sauvegarder le thème dans la BD
        self.db_manager.save_user_theme(theme_name)

        # Émettre le signal de changement de thème
        self.theme_changed.emit(theme_name)

    def show_export_import_dialog(self):
        """Affiche le dialogue d'exportation/importation"""
        dialog = ExportImportDialog(self, self.db_manager)
        dialog.exec()

    def create_backup(self):
        """Crée une sauvegarde de la base de données actuelle"""
        try:
            # Chemin de la base de données actuelle
            db_path = self.db_manager.db_file
            db_dir = os.path.dirname(db_path)
            db_name = os.path.basename(db_path)

            # Générer un nom de fichier avec timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(db_name)[0]}.db.{timestamp}.bak"
            backup_path = os.path.join(db_dir, backup_filename)

            # Copier le fichier actuel comme sauvegarde
            shutil.copy2(db_path, backup_path)

            # Informer l'utilisateur
            QMessageBox.information(
                self,
                "Sauvegarde créée",
                f"Une sauvegarde de la base de données a été créée avec succès.\n\n"
                f"Emplacement: {backup_path}",
            )

        except (OSError, shutil.Error) as e:
            # En cas d'erreur liée au système de fichiers ou à la copie
            QMessageBox.critical(
                self,
                "Erreur de sauvegarde",
                f"Une erreur est survenue lors de la création de la sauvegarde:\n\n{str(e)}",
            )
            traceback.print_exc()

    def reset_database(self):
        """Réinitialise la base de données après confirmation de l'utilisateur"""
        # Demander confirmation avec un dialogue personnalisé
        dialog = ResetDBConfirmDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        create_backup = dialog.backup_checkbox.isChecked()

        try:
            # Chemin de la base de données actuelle
            db_path = self.db_manager.db_file

            # Créer une sauvegarde si demandé
            if create_backup:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{db_path}.{timestamp}.bak"

                # Copier le fichier actuel comme sauvegarde
                shutil.copy2(db_path, backup_path)
                print(f"Sauvegarde créée: {backup_path}")

            # Fermer toutes les connexions à la base de données
            self.db_manager.disconnect()

            # Supprimer le fichier de base de données actuel
            os.remove(db_path)
            print(f"Base de données supprimée: {db_path}")

            # Réinitialiser les variables de classe du singleton DBConnector
            DBConnector.reset_instance()
            DBConnector.reset_db_path_logged()

            # Réinitialiser le gestionnaire de base de données
            # Cela réinitialisera toutes les tables et créera un utilisateur par défaut
            self.db_manager = type(
                self.db_manager
            )()  # Crée une nouvelle instance du même type
            self.db_manager.init_db()

            # Mettre à jour la référence à db_manager dans l'application
            main_window = QApplication.activeWindow()

            if main_window and main_window.__class__.__name__ == "MainWindow":
                # Mettre à jour le gestionnaire de base de données dans la fenêtre principale
                main_window.db_manager = self.db_manager

                # Mettre à jour les références dans tous les onglets
                # Accès direct aux attributs d'onglets nommés
                tab_attributes = [
                    "utilisateur_tab",
                    "aliments_tab",
                    "planning_tab",
                    "recettes_tab",
                    "courses_tab",
                    "options_tab",
                ]

                for attr in tab_attributes:
                    if hasattr(main_window, attr):
                        tab = getattr(main_window, attr)
                        if hasattr(tab, "db_manager"):
                            tab.db_manager = self.db_manager

                # Rafraîchir tous les onglets
                if hasattr(main_window, "refresh_all_tabs"):
                    main_window.refresh_all_tabs()

            # Appliquer le thème par défaut
            default_theme = "Vert Nature"
            self.theme_manager = ThemeManager(self.db_manager)
            index = self.theme_combo.findText(default_theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

            # Informer l'utilisateur
            QMessageBox.information(
                self,
                "Base de données réinitialisée",
                "La base de données a été réinitialisée avec succès. "
                "Toutes les données ont été supprimées et les valeurs par défaut ont été restaurées."
                + (
                    f"\n\nUne sauvegarde a été créée: {backup_path}"
                    if create_backup
                    else ""
                ),
            )

        except (OSError, shutil.Error) as e:
            # En cas d'erreur liée au système de fichiers ou à la copie
            QMessageBox.critical(
                self,
                "Erreur de réinitialisation",
                f"Une erreur liée au système de fichiers est survenue lors de la réinitialisation de la base de données:\n\n{str(e)}",
            )
            traceback.print_exc()
        except (ValueError, RuntimeError) as e:
            # En cas d'autres erreurs spécifiques imprévues
            QMessageBox.critical(
                self,
                "Erreur de réinitialisation",
                f"Une erreur imprévue est survenue lors de la réinitialisation de la base de données:\n\n{str(e)}",
            )
            traceback.print_exc()

    def restore_database(self):
        """Restaure la base de données à partir d'une sauvegarde"""
        # Dossier des sauvegardes (dans le même dossier que la base de données)
        backup_dir = os.path.dirname(self.db_manager.db_file)

        # Ouvrir la boîte de dialogue de sélection de sauvegarde
        dialog = BackupSelectDialog(self, backup_dir)
        if dialog.exec() != QDialog.Accepted:
            return

        # Obtenir le chemin de la sauvegarde sélectionnée
        backup_path = dialog.get_selected_backup()
        if not backup_path or not os.path.exists(backup_path):
            QMessageBox.warning(
                self,
                "Restauration impossible",
                "Aucune sauvegarde valide n'a été sélectionnée.",
            )
            return

        # Confirmer avec l'utilisateur
        reply = QMessageBox.question(
            self,
            "Confirmer la restauration",
            "Êtes-vous sûr de vouloir restaurer cette sauvegarde?\n\n"
            "La base de données actuelle sera remplacée et l'application redémarrée.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Chemin de la base de données actuelle
        db_path = self.db_manager.db_file

        try:
            # Fermer toutes les connexions à la base de données
            self.db_manager.disconnect()

            # Important: réinitialiser l'instance singleton pour fermer toutes les connexions
            db_connector = DBConnector()
            db_connector.force_close_all_connections()

            # Attendre un court instant pour que Windows libère les ressources
            time.sleep(0.5)

            # Créer une sauvegarde de la base de données actuelle avant restauration
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_backup_path = os.path.join(
                os.path.dirname(db_path),
                f"nutrition_sportive.db.{timestamp}.auto_backup.bak",
            )

            # Essayer de faire une copie de sécurité
            try:
                shutil.copy2(db_path, auto_backup_path)
                print(f"Sauvegarde automatique créée: {auto_backup_path}")
            except (OSError, shutil.Error) as e:
                print(f"Impossible de créer une sauvegarde automatique: {e}")

            # Essayer de supprimer le fichier actuel
            try:
                os.remove(db_path)
            except PermissionError:
                # Si la suppression échoue, essayer une autre approche
                print(
                    "Première tentative de suppression échouée, essai avec une approche alternative..."
                )

                # Forcer la collecte des déchets pour libérer les ressources
                gc.collect()
                time.sleep(1)

                # Essayer de renommer plutôt que supprimer
                temp_path = db_path + ".old"
                os.rename(db_path, temp_path)

                # Après avoir renommé, essayer de supprimer le fichier renommé
                try:
                    os.remove(temp_path)
                except (OSError, shutil.Error, PermissionError) as e:
                    print(
                        f"Fichier renommé en {temp_path}, impossible de le supprimer: {e}"
                    )

            # Copier la sauvegarde vers l'emplacement de la base de données
            shutil.copy2(backup_path, db_path)

            # Informer l'utilisateur que la restauration a réussi
            QMessageBox.information(
                self,
                "Restauration réussie",
                "La base de données a été restaurée avec succès.\n\n"
                "L'application va maintenant redémarrer pour appliquer les changements.",
            )

            # Redémarrer l'application
            restart_application()

        except (OSError, shutil.Error, PermissionError, RuntimeError) as e:
            QMessageBox.critical(
                self,
                "Erreur de restauration",
                f"Une erreur est survenue lors de la restauration de la base de données:\n\n{str(e)}",
            )
            print(f"Erreur de restauration: {e}")

            # En cas d'erreur, essayer de réinitialiser la connexion
            try:
                self.db_manager.connect()
            except RuntimeError as reconnect_error:
                print(f"Error reconnecting to the database: {reconnect_error}")

    def refresh_data(self):
        """Rafraîchit les données affichées (pas nécessaire pour cet onglet)"""
