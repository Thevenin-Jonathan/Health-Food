import json
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QCheckBox,
    QMessageBox,
    QProgressBar,
    QComboBox,
)
from PySide6.QtCore import Qt
from src.utils.events import EVENT_BUS


class ExportImportDialog(QDialog):
    """Dialogue pour exporter et importer des données"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Exportation / Importation des données")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Titre
        title_label = QLabel("<h2>Exportation et Importation</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Section d'exportation
        export_group = QGroupBox("Exportation des données")
        export_layout = QVBoxLayout(export_group)

        # Options d'exportation
        self.export_aliments_cb = QCheckBox("Aliments")
        self.export_recettes_cb = QCheckBox("Recettes")
        self.export_planning_cb = QCheckBox("Planning hebdomadaire")

        export_layout.addWidget(self.export_aliments_cb)
        export_layout.addWidget(self.export_recettes_cb)
        export_layout.addWidget(self.export_planning_cb)

        # Semaine pour l'exportation du planning
        planning_layout = QHBoxLayout()
        planning_layout.addWidget(QLabel("Semaine:"))
        self.export_semaine_combo = QComboBox()
        self.charger_semaines()
        planning_layout.addWidget(self.export_semaine_combo)
        export_layout.addLayout(planning_layout)

        # Bouton d'exportation
        self.export_btn = QPushButton("Exporter")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.clicked.connect(self.exporter_donnees)
        export_layout.addWidget(self.export_btn)

        main_layout.addWidget(export_group)

        # Section d'importation
        import_group = QGroupBox("Importation des données")
        import_layout = QVBoxLayout(import_group)

        # Options d'importation
        self.import_aliments_cb = QCheckBox("Aliments")
        self.import_recettes_cb = QCheckBox("Recettes")
        self.import_planning_cb = QCheckBox("Planning hebdomadaire")

        import_layout.addWidget(self.import_aliments_cb)
        import_layout.addWidget(self.import_recettes_cb)
        import_layout.addWidget(self.import_planning_cb)

        # Bouton d'importation
        self.import_btn = QPushButton("Importer")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.clicked.connect(self.importer_donnees)
        import_layout.addWidget(self.import_btn)

        main_layout.addWidget(import_group)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Boutons du bas
        buttons_layout = QHBoxLayout()
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)

        main_layout.addLayout(buttons_layout)

    def charger_semaines(self):
        """Charge les semaines disponibles dans la combobox"""
        self.export_semaine_combo.clear()

        self.export_semaine_combo.addItem("Semaine courante", None)

        # Ajouter toutes les semaines existantes
        semaines = self.db_manager.get_semaines_existantes()
        for semaine_id in semaines:
            self.export_semaine_combo.addItem(f"Semaine {semaine_id}", semaine_id)

    def exporter_donnees(self):
        """Exporte les données sélectionnées vers un fichier JSON"""
        # Vérifier qu'au moins une option est sélectionnée
        if not (
            self.export_aliments_cb.isChecked()
            or self.export_recettes_cb.isChecked()
            or self.export_planning_cb.isChecked()
        ):
            QMessageBox.warning(
                self,
                "Aucune donnée sélectionnée",
                "Veuillez sélectionner au moins un type de données à exporter.",
            )
            return

        # Ouvrir la boîte de dialogue pour choisir l'emplacement du fichier
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"health_food_export_{date_str}.json"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'exportation",
            default_filename,
            "Fichiers JSON (*.json)",
        )

        if not filepath:
            return

        # Préparer les données à exporter
        export_data = {}

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Exporter les aliments
        if self.export_aliments_cb.isChecked():
            export_data["aliments"] = self.db_manager.exporter_aliments()
            self.progress_bar.setValue(33)

        # Exporter les recettes
        if self.export_recettes_cb.isChecked():
            export_data["repas_types"] = self.db_manager.exporter_repas_types()
            self.progress_bar.setValue(66)

        # Exporter le planning
        if self.export_planning_cb.isChecked():
            semaine_id = self.export_semaine_combo.currentData()
            export_data["planning"] = self.db_manager.exporter_planning(semaine_id)
            self.progress_bar.setValue(100)

        # Sauvegarder les données dans un fichier JSON
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)

            QMessageBox.information(
                self,
                "Exportation réussie",
                f"Les données ont été exportées avec succès vers {filepath}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur lors de l'exportation",
                f"Une erreur est survenue lors de l'exportation des données: {str(e)}",
            )

        self.progress_bar.setVisible(False)

    def importer_donnees(self):
        """Importe les données depuis un fichier JSON"""
        # Vérifier qu'au moins une option est sélectionnée
        if not (
            self.import_aliments_cb.isChecked()
            or self.import_recettes_cb.isChecked()
            or self.import_planning_cb.isChecked()
        ):
            QMessageBox.warning(
                self,
                "Aucune donnée sélectionnée",
                "Veuillez sélectionner au moins un type de données à importer.",
            )
            return

        # Ouvrir la boîte de dialogue pour choisir le fichier à importer
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir le fichier d'importation", "", "Fichiers JSON (*.json)"
        )

        if not filepath:
            return

        # Charger les données du fichier JSON
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                import_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur lors de l'importation",
                f"Impossible de lire le fichier JSON: {str(e)}",
            )
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        import_summary = []

        # Importer les aliments
        if self.import_aliments_cb.isChecked() and "aliments" in import_data:
            count = self.db_manager.importer_aliments(import_data["aliments"])
            import_summary.append(f"{count} aliments importés")
            self.progress_bar.setValue(33)

        # Importer les recettes
        if self.import_recettes_cb.isChecked() and "repas_types" in import_data:
            count = self.db_manager.importer_repas_types(import_data["repas_types"])
            import_summary.append(f"{count} recettes importées")
            self.progress_bar.setValue(66)

        # Importer le planning
        if self.import_planning_cb.isChecked() and "planning" in import_data:
            count = self.db_manager.importer_planning(import_data["planning"])
            import_summary.append(f"{count} repas importés dans le planning")
            self.progress_bar.setValue(100)

        # Signaler que des données ont été importées
        EVENT_BUS.donnees_importees.emit()

        # Afficher un résumé de l'importation
        if import_summary:
            QMessageBox.information(
                self,
                "Importation réussie",
                "Résumé de l'importation:\n" + "\n".join(import_summary),
            )
        else:
            QMessageBox.warning(
                self,
                "Aucune donnée importée",
                "Aucune des données sélectionnées n'a été trouvée dans le fichier.",
            )

        self.progress_bar.setVisible(False)

        # Recharger les semaines disponibles
        self.charger_semaines()
