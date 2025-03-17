from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSpinBox,
    QFormLayout,
    QLineEdit,
    QWidget,
    QMessageBox,
)


class RepasDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, semaine_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.semaine_id = semaine_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un repas")
        self.setMinimumWidth(300)

        layout = QFormLayout()

        # Option pour choisir entre un nouveau repas ou une recette existante
        self.type_choix = QComboBox()
        self.type_choix.addItems(["Nouveau repas", "Utiliser une recette existante"])
        self.type_choix.currentIndexChanged.connect(self.toggle_mode)
        layout.addRow("Type:", self.type_choix)

        # Widget pour contenir les champs spécifiques au mode
        self.mode_widget = QWidget()
        self.mode_layout = QFormLayout(self.mode_widget)

        # Mode nouveau repas
        self.nom_input = QLineEdit()
        self.mode_layout.addRow("Nom du repas:", self.nom_input)

        # Mode recette
        self.recette_combo = QComboBox()
        self.recette_combo.hide()
        self.charger_recettes()
        self.mode_layout.addRow("Recette:", self.recette_combo)

        layout.addRow(self.mode_widget)

        # Sélection du jour (commun aux deux modes)
        self.jour_input = QComboBox()
        self.jour_input.addItems(
            ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        )
        layout.addRow("Jour:", self.jour_input)

        # Ordre dans la journée (commun aux deux modes) - Avec style amélioré
        self.ordre_input = QSpinBox()
        self.ordre_input.setMinimum(1)
        self.ordre_input.setValue(1)
        self.ordre_input.setFixedHeight(30)  # Augmenter la hauteur
        self.ordre_input.setStyleSheet(
            """
            QSpinBox { 
                padding-right: 15px; /* Espace pour les flèches */
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px; /* Augmenter la largeur des boutons */
                height: 14px; /* Définir la hauteur des boutons */
                padding: 0px;
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
            }
        """
        )
        layout.addRow("Ordre:", self.ordre_input)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.validate_and_accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

        # Initialiser le mode
        self.toggle_mode(0)

    def charger_recettes(self):
        """Charge les recettes disponibles dans le combobox"""
        if not self.db_manager:
            return

        self.recette_combo.clear()
        self.recettes = self.db_manager.get_repas_types()

        self.recette_ids = [recette["id"] for recette in self.recettes]

        for recette in self.recettes:
            self.recette_combo.addItem(recette["nom"])

    def toggle_mode(self, index):
        """Change le mode entre nouveau repas et recette existante"""
        if index == 0:  # Nouveau repas
            self.nom_input.show()
            self.recette_combo.hide()
        else:  # Recette existante
            self.nom_input.hide()
            self.recette_combo.show()

    def validate_and_accept(self):
        """Valide les données avant d'accepter"""
        if self.type_choix.currentIndex() == 0 and not self.nom_input.text().strip():
            QMessageBox.warning(
                self, "Champ obligatoire", "Le nom du repas est obligatoire."
            )
            return
        elif self.type_choix.currentIndex() == 1 and self.recette_combo.count() == 0:
            QMessageBox.warning(
                self,
                "Aucune recette",
                "Aucune recette disponible. Veuillez en créer une d'abord.",
            )
            return

        self.accept()

    def get_data(self):
        """Retourne les données du formulaire"""
        if self.type_choix.currentIndex() == 0:
            # Nouveau repas
            return (
                self.nom_input.text().strip(),
                self.jour_input.currentText(),
                self.ordre_input.value(),
                None,  # Pas de recette sélectionnée
            )
        else:
            # Recette existante
            if self.recette_combo.count() > 0:
                recette_id = self.recette_ids[self.recette_combo.currentIndex()]
                return (
                    None,  # Pas besoin de nom, on utilise celui de la recette
                    self.jour_input.currentText(),
                    self.ordre_input.value(),
                    recette_id,
                )
            return (None, None, None, None)
