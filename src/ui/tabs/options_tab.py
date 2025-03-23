from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QWidget,
    QComboBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal
from src.ui.dialogs.export_import_dialog import ExportImportDialog
from src.utils.theme_manager import ThemeManager
from .tab_base import TabBase


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

    def refresh_data(self):
        """Rafraîchit les données affichées (pas nécessaire pour cet onglet)"""
        pass
