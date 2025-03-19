from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QCompleter,
    QGroupBox,
    QGridLayout,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from src.ui.components.recent_value_button import RecentValueButton
from src.ui.components.nutrition_input import create_nutrition_spinbox
from src.utils.text_utils import normalize_str


class AlimentDialog(QDialog):
    """Dialogue pour ajouter ou modifier un aliment"""

    def __init__(
        self, parent=None, aliment=None, magasins=None, marques=None, categories=None
    ):
        super().__init__(parent)
        self.aliment = aliment
        self.magasins = magasins or []
        self.marques = marques or []
        self.categories = categories or []
        # Champs d'information
        self.nom_input = None
        self.marque_input = None
        self.magasin_input = None
        self.categorie_input = None
        self.prix_kg_input = None

        # Champs nutritionnels
        self.calories_input = None
        self.proteines_input = None
        self.glucides_input = None
        self.lipides_input = None
        self.fibres_input = None

        # Boutons
        self.btn_cancel = None
        self.btn_save = None

        # Initialiser l'interface
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter/Modifier un aliment")
        self.setMinimumWidth(550)
        self.setMinimumHeight(550)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Ajouter les différentes parties
        self._setup_info_group(main_layout)
        self._setup_nutrition_group(main_layout)

        # Étirer le layout pour remplir l'espace
        main_layout.addStretch()

        # Ajouter les boutons d'action
        self._setup_buttons(main_layout)

        # Si on modifie un aliment existant, remplir les champs
        if self.aliment:
            self.fill_data_from_aliment()

    def _setup_info_group(self, main_layout):
        """Configure le groupe d'informations générales"""
        info_group = QGroupBox("Informations générales")
        info_layout = QFormLayout()

        # Champ Nom
        self.nom_input = QLineEdit()
        info_layout.addRow("Nom:", self.nom_input)

        # Champ Marque avec autocomplétion et boutons récents
        self.marque_input = self._create_input_with_buttons(
            self.marques, "marque_input"
        )
        info_layout.addRow("Marque:", self.marque_input)

        # Champ Magasin avec autocomplétion et boutons récents
        self.magasin_input = self._create_input_with_buttons(
            self.magasins, "magasin_input"
        )
        info_layout.addRow("Magasin:", self.magasin_input)

        # Configuration de la combobox Catégorie
        self._setup_category_combo()
        info_layout.addRow("Catégorie:", self.categorie_input)

        # Champ Prix
        prix_container = self._setup_price_field()
        info_layout.addRow("Prix au kg:", prix_container)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

    def _create_input_with_buttons(self, items, input_name):
        """Crée un champ avec autocomplétion et boutons de valeurs récentes"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Créer le champ avec auto-complétion
        input_field = QLineEdit()
        completer = QCompleter(items)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        input_field.setCompleter(completer)
        layout.addWidget(input_field)

        # Ajouter la référence au champ comme attribut de la classe
        setattr(self, input_name, input_field)

        # Ajouter les boutons pour les valeurs récentes
        recent_items = items[:5] if len(items) >= 5 else items
        if recent_items:
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(5)

            for index, item in enumerate(recent_items):
                btn = RecentValueButton(item, color_index=index)
                btn.clicked.connect(
                    lambda checked, i=item, field=input_field: field.setText(i)
                )
                buttons_layout.addWidget(btn)

            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)

        return container

    def _setup_category_combo(self):
        """Configure la combobox des catégories"""
        self.categorie_input = QComboBox()
        self.categorie_input.setEditable(True)

        # Fusionner et trier les catégories
        predefined_categories = [
            "Fruits",
            "Légumes",
            "Viandes",
            "Poissons",
            "Produits laitiers",
            "Féculents",
            "Boissons",
            "Snacks",
            "Sucreries",
            "Épices et condiments",
            "Compléments alimentaires",
            "Autre",
        ]

        all_categories = set(predefined_categories)
        for cat in self.categories:
            if cat:
                all_categories.add(cat)

        # Trier et ajouter au combobox
        sorted_categories = sorted(all_categories, key=normalize_str)
        for categorie in sorted_categories:
            self.categorie_input.addItem(categorie)

        # Sélectionner "Autre" par défaut
        default_index = self.categorie_input.findText("Autre")
        if default_index >= 0:
            self.categorie_input.setCurrentIndex(default_index)

    def _setup_price_field(self):
        """Configure le champ de prix avec son unité"""
        prix_container = QWidget()
        prix_layout = QHBoxLayout(prix_container)
        prix_layout.setContentsMargins(0, 0, 0, 0)
        prix_layout.setSpacing(5)

        self.prix_kg_input = QLineEdit()
        self.prix_kg_input.setPlaceholderText("0.00")
        validator = QDoubleValidator(0, 9999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.prix_kg_input.setValidator(validator)
        self.prix_kg_input.setFixedWidth(100)

        prix_layout.addWidget(self.prix_kg_input)
        prix_layout.addWidget(QLabel("€/kg"))
        prix_layout.addStretch()

        return prix_container

    def _setup_nutrition_group(self, main_layout):
        """Configure le groupe des valeurs nutritionnelles"""
        nutrition_group = QGroupBox("Valeurs nutritionnelles (pour 100g)")
        nutrition_layout = QGridLayout()

        self.calories_input = create_nutrition_spinbox(0, 1000, " kcal", 0)
        self.proteines_input = create_nutrition_spinbox(0, 100, " g", 1)
        self.glucides_input = create_nutrition_spinbox(0, 100, " g", 1)
        self.lipides_input = create_nutrition_spinbox(0, 100, " g", 1)
        self.fibres_input = create_nutrition_spinbox(0, 100, " g", 1)

        nutrition_layout.addWidget(QLabel("Calories:"), 0, 0)
        nutrition_layout.addWidget(self.calories_input, 0, 1)

        nutrition_layout.addWidget(QLabel("Protéines:"), 0, 2)
        nutrition_layout.addWidget(self.proteines_input, 0, 3)

        nutrition_layout.addWidget(QLabel("Glucides:"), 1, 0)
        nutrition_layout.addWidget(self.glucides_input, 1, 1)

        nutrition_layout.addWidget(QLabel("Lipides:"), 1, 2)
        nutrition_layout.addWidget(self.lipides_input, 1, 3)

        nutrition_layout.addWidget(QLabel("Fibres:"), 2, 0)
        nutrition_layout.addWidget(self.fibres_input, 2, 1)

        nutrition_group.setLayout(nutrition_layout)
        main_layout.addWidget(nutrition_group)

    def _setup_buttons(self, main_layout):
        """Configure les boutons en bas de dialogue"""
        buttons_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            """
        )

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_save)

        main_layout.addLayout(buttons_layout)

    def fill_data_from_aliment(self):
        """Remplit les champs avec les données de l'aliment à modifier"""
        self.nom_input.setText(self.aliment["nom"])
        self.marque_input.setText(self.aliment["marque"] or "")
        self.magasin_input.setText(self.aliment["magasin"] or "")

        # Gestion spéciale pour la catégorie
        categorie = self.aliment["categorie"] or ""
        index = self.categorie_input.findText(categorie)
        if index >= 0:
            self.categorie_input.setCurrentIndex(index)
        elif categorie:
            self.categorie_input.addItem(categorie)
            self.categorie_input.setCurrentText(categorie)

        # Prix
        if self.aliment["prix_kg"]:
            self.prix_kg_input.setText(f"{self.aliment['prix_kg']:.2f}")
        else:
            self.prix_kg_input.setText("")

        # Valeurs nutritionnelles
        self.calories_input.setValue(self.aliment["calories"] or 0)
        self.proteines_input.setValue(self.aliment["proteines"] or 0)
        self.glucides_input.setValue(self.aliment["glucides"] or 0)
        self.lipides_input.setValue(self.aliment["lipides"] or 0)
        self.fibres_input.setValue(self.aliment["fibres"] or 0)

    def accept(self):
        """Vérification des données avant d'accepter le dialogue"""
        missing_fields = []

        if not self.nom_input.text().strip():
            missing_fields.append("Nom")

        if not self.marque_input.text().strip():
            missing_fields.append("Marque")

        if not self.magasin_input.text().strip():
            missing_fields.append("Magasin")

        if not self.categorie_input.currentText().strip():
            missing_fields.append("Catégorie")

        if missing_fields:
            QMessageBox.warning(
                self,
                "Champs obligatoires",
                f"Tous les champs suivants sont obligatoires :\n\n{', '.join(missing_fields)}",
            )
            return

        super().accept()

    def get_data(self):
        """Retourne les données saisies sous forme de dictionnaire"""
        prix_text = self.prix_kg_input.text().strip()

        try:
            prix_kg = float(prix_text.replace(",", ".")) if prix_text else None
        except ValueError:
            prix_kg = None

        return {
            "nom": self.nom_input.text().strip(),
            "marque": self.marque_input.text().strip(),
            "magasin": self.magasin_input.text().strip(),
            "categorie": self.categorie_input.currentText().strip(),
            "calories": self.calories_input.value(),
            "proteines": self.proteines_input.value(),
            "glucides": self.glucides_input.value(),
            "lipides": self.lipides_input.value(),
            "fibres": self.fibres_input.value(),
            "prix_kg": prix_kg,
        }
