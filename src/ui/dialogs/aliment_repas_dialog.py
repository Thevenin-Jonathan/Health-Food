from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
)
from src.utils import AutoSelectDoubleSpinBox


class AlimentRepasDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.aliment_ids = []
        self.aliment_combo = None
        self.quantite_input = None
        self.info_label = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un aliment au repas")
        self.setMinimumWidth(350)

        layout = QFormLayout()

        # Sélection de l'aliment
        self.aliment_combo = QComboBox()
        self.load_aliments()
        layout.addRow("Aliment:", self.aliment_combo)

        # Quantité en grammes avec style amélioré pour une meilleure manipulation
        self.quantite_input = AutoSelectDoubleSpinBox()
        self.quantite_input.setMinimum(1)
        self.quantite_input.setMaximum(5000)
        self.quantite_input.setValue(100)
        self.quantite_input.setSuffix(" g")
        # Configuration pour une meilleure utilisation des flèches
        self.quantite_input.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self.quantite_input.setSingleStep(10)  # Incrément de 10g par défaut
        self.quantite_input.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        # Style pour les boutons verticaux
        self.quantite_input.setProperty("class", "spin-box-vertical")
        layout.addRow("Quantité:", self.quantite_input)

        # Informations sur l'aliment sélectionné
        self.info_label = QLabel("")
        self.info_label.setProperty("class", "nutrition-info")
        self.info_label.setWordWrap(True)  # Permettre le retour à la ligne
        layout.addRow("Valeurs nutritionnelles:", self.info_label)

        # Mettre à jour les informations quand on change d'aliment
        self.aliment_combo.currentIndexChanged.connect(self.update_info)
        self.quantite_input.valueChanged.connect(self.update_info)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Ajouter")
        self.btn_save.setObjectName("saveButton")
        self.btn_save.clicked.connect(self.validate_and_accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

        # Mettre à jour les informations immédiatement si un aliment est disponible
        if self.aliment_combo.count() > 0:
            self.update_info()

    def load_aliments(self):
        aliments = self.db_manager.get_aliments(sort_column="nom", sort_order=True)
        self.aliment_ids = [aliment["id"] for aliment in aliments]

        for aliment in aliments:
            self.aliment_combo.addItem(
                f"{aliment['nom']} ({aliment['marque'] or 'Sans marque'})"
            )

    def update_info(self):
        if self.aliment_combo.currentIndex() >= 0:
            aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
            aliment = self.db_manager.get_aliment(aliment_id)
            quantite = self.quantite_input.value()

            # Calculer les valeurs pour la quantité spécifiée
            calories = aliment["calories"] * quantite / 100
            proteines = aliment["proteines"] * quantite / 100
            glucides = aliment["glucides"] * quantite / 100
            lipides = aliment["lipides"] * quantite / 100

            # Affichage des valeurs uniquement pour la quantité sélectionnée
            info_text = f"<b>Calories:</b> {calories:.0f} kcal<br>"
            info_text += f"<b>Protéines:</b> {proteines:.1f}g<br>"
            info_text += f"<b>Glucides:</b> {glucides:.1f}g<br>"
            info_text += f"<b>Lipides:</b> {lipides:.1f}g"

            # Ajouter les fibres si disponibles
            if aliment.get("fibres"):
                fibres = aliment["fibres"] * quantite / 100
                info_text += f"<br><b>Fibres:</b> {fibres:.1f}g"

            self.info_label.setText(info_text)
        else:
            self.info_label.setText("Aucun aliment disponible")

    def validate_and_accept(self):
        if self.aliment_combo.currentIndex() < 0:
            QMessageBox.warning(
                self, "Sélection requise", "Veuillez sélectionner un aliment."
            )
            return

        self.accept()

    def get_data(self):
        aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
        return (aliment_id, self.quantite_input.value())
