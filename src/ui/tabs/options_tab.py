from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QWidget,
)
from PySide6.QtCore import Qt
from src.ui.dialogs.export_import_dialog import ExportImportDialog
from .tab_base import TabBase


class OptionsTab(TabBase):
    """Onglet des options de l'application"""

    def __init__(self, db_manager):
        super().__init__(db_manager)
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

        # Ajouter d'autres groupes d'options si nécessaire...

        # Ajouter un espace extensible en bas
        main_layout.addStretch()

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

    def show_export_import_dialog(self):
        """Affiche le dialogue d'exportation/importation"""
        dialog = ExportImportDialog(self, self.db_manager)
        dialog.exec()

    def refresh_data(self):
        """Rafraîchit les données affichées (pas nécessaire pour cet onglet)"""
        pass
