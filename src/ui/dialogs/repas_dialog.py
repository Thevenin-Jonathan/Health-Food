from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QSpinBox,
    QFormLayout,
    QLineEdit,
    QLabel,
)

from src.utils.config import JOURS_SEMAINE


class RepasDialog(QDialog):
    def __init__(
        self, parent=None, db_manager=None, semaine_id=None, jour_predefini=None
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.semaine_id = semaine_id
        self.jour_predefini = jour_predefini

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un repas")
        self.setMinimumWidth(400)

        self.layout = QFormLayout()

        # Nom du repas
        self.nom_input = QLineEdit()
        self.layout.addRow("Nom du repas:", self.nom_input)

        # Jour - visible uniquement si jour_predefini n'est pas spécifié
        self.jour_input = QComboBox()
        if self.jour_predefini is None:
            self.jour_input.addItems(JOURS_SEMAINE)
            self.layout.addRow("Jour:", self.jour_input)
        else:
            # Créer le combobox mais le cacher, afin que la même méthode get_data() fonctionne
            self.jour_input.addItems(JOURS_SEMAINE)
            self.jour_input.setCurrentText(self.jour_predefini)
            self.jour_input.hide()

        # Ordre dans la journée
        self.ordre_input = QSpinBox()
        self.ordre_input.setProperty("class", "spin-box-vertical")
        self.ordre_input.setMinimum(1)
        self.ordre_input.setValue(1)
        self.layout.addRow("Position dans la journée:", self.ordre_input)

        # Utiliser une recette existante
        self.repas_type_label = QLabel("Utiliser une recette existante (optionnel):")
        self.layout.addRow(self.repas_type_label)

        self.repas_type_input = QComboBox()
        self.repas_type_input.addItem(
            "Aucune", None
        )  # Option pour ne pas utiliser de recette
        self.layout.addRow(self.repas_type_input)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Ajouter")
        self.btn_save.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        self.layout.addRow(btn_layout)

        self.setLayout(self.layout)

    def load_data(self):
        """Charge les recettes existantes"""
        repas_types = self.db_manager.get_repas_types()

        for repas_type in repas_types:
            self.repas_type_input.addItem(
                f"{repas_type['nom']} ({repas_type['total_calories']:.0f} kcal)",
                repas_type["id"],
            )

    def get_data(self):
        """Récupère les données saisies"""
        # Utiliser le jour prédéfini si disponible, sinon prendre celui du combobox
        jour = (
            self.jour_predefini
            if self.jour_predefini
            else self.jour_input.currentText()
        )

        return (
            self.nom_input.text().strip(),
            jour,
            self.ordre_input.value(),
            self.repas_type_input.currentData(),
        )
