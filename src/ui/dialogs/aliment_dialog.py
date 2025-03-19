import unicodedata
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDoubleSpinBox,
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


class RecentValueButton(QPushButton):
    """Bouton pour sélectionner une valeur récemment utilisée"""

    def __init__(self, text, value=None, parent=None, color_index=0):
        super().__init__(text, parent)
        self.value = value if value is not None else text

        # Liste de couleurs pour les boutons récents (plus vives et distinctes)
        colors = [
            "#4CAF50",  # Vert
            "#2196F3",  # Bleu
            "#FF9800",  # Orange
            "#9C27B0",  # Violet
            "#E91E63",  # Rose
        ]

        # Sélectionner une couleur en fonction de l'index (modulo pour éviter les dépassements)
        color = colors[color_index % len(colors)]

        # Style avec couleur de fond distincte pour une meilleure visibilité
        self.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 8px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}99;  /* Ajout d'une transparence au survol */
            }}
        """
        )


class AlimentDialog(QDialog):
    """Dialogue pour ajouter ou modifier un aliment"""

    def __init__(
        self, parent=None, aliment=None, magasins=None, marques=None, categories=None
    ):
        super().__init__(parent)
        self.aliment = (
            aliment  # None pour un nouvel aliment, sinon l'aliment à modifier
        )
        self.magasins = magasins or []
        self.marques = marques or []
        self.categories = categories or []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter/Modifier un aliment")
        self.setMinimumWidth(550)
        self.setMinimumHeight(550)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # ---------- Groupe Informations de base ----------
        info_group = QGroupBox("Informations générales")
        info_layout = QFormLayout()

        # Champs de saisie principaux - tous obligatoires
        self.nom_input = QLineEdit()
        info_layout.addRow("Nom:", self.nom_input)

        # Groupe pour la marque et ses boutons récents
        marque_container = QWidget()
        marque_layout = QVBoxLayout(marque_container)
        marque_layout.setContentsMargins(0, 0, 0, 0)
        marque_layout.setSpacing(5)

        # Champ de marque avec auto-complétion
        self.marque_input = QLineEdit()
        marque_completer = QCompleter(self.marques)
        marque_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.marque_input.setCompleter(marque_completer)
        marque_layout.addWidget(self.marque_input)

        # Boutons pour les marques récentes
        marques_recentes = self.marques[:5] if len(self.marques) >= 5 else self.marques
        if marques_recentes:
            marque_buttons_layout = QHBoxLayout()
            marque_buttons_layout.setSpacing(5)

            for index, marque in enumerate(marques_recentes):
                btn = RecentValueButton(marque, color_index=index)
                btn.clicked.connect(
                    lambda checked, m=marque: self.marque_input.setText(m)
                )
                marque_buttons_layout.addWidget(btn)

            marque_buttons_layout.addStretch()
            marque_layout.addLayout(marque_buttons_layout)

        info_layout.addRow("Marque:", marque_container)

        # Groupe pour le magasin et ses boutons récents
        magasin_container = QWidget()
        magasin_layout = QVBoxLayout(magasin_container)
        magasin_layout.setContentsMargins(0, 0, 0, 0)
        magasin_layout.setSpacing(5)

        # Champ de magasin avec auto-complétion
        self.magasin_input = QLineEdit()
        magasin_completer = QCompleter(self.magasins)
        magasin_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.magasin_input.setCompleter(magasin_completer)
        magasin_layout.addWidget(self.magasin_input)

        # Boutons pour les magasins récents
        magasins_recents = (
            self.magasins[:5] if len(self.magasins) >= 5 else self.magasins
        )
        if magasins_recents:
            magasin_buttons_layout = QHBoxLayout()
            magasin_buttons_layout.setSpacing(5)

            for index, magasin in enumerate(magasins_recents):
                btn = RecentValueButton(magasin, color_index=index)
                btn.clicked.connect(
                    lambda checked, m=magasin: self.magasin_input.setText(m)
                )
                magasin_buttons_layout.addWidget(btn)

            magasin_buttons_layout.addStretch()
            magasin_layout.addLayout(magasin_buttons_layout)

        info_layout.addRow("Magasin:", magasin_container)

        # Champ catégorie - ComboBox avec catégories prédéfinies ET existantes
        self.categorie_input = QComboBox()
        self.categorie_input.setEditable(True)  # Permettre la saisie libre

        # Catégories prédéfinies
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

        # Fusionner les catégories prédéfinies et celles de la base de données
        all_categories = set()

        # Ajouter d'abord les catégories prédéfinies
        for cat in predefined_categories:
            all_categories.add(cat)

        # Puis ajouter les catégories de la base de données
        for cat in self.categories:
            if cat:  # Vérifier que la catégorie n'est pas vide
                all_categories.add(cat)

        # Normaliser et trier les catégories (pour gérer correctement les accents)
        def normalize_str(s):
            """Normalise une chaîne en supprimant les accents pour le tri"""
            if not s:
                return ""
            return (
                unicodedata.normalize("NFKD", s)
                .encode("ASCII", "ignore")
                .decode("ASCII")
                .lower()
            )

        # Trier les catégories en tenant compte de la normalisation
        sorted_categories = sorted(all_categories, key=normalize_str)

        # Ajouter au ComboBox
        for categorie in sorted_categories:
            self.categorie_input.addItem(categorie)

        # Sélectionner "Autre" par défaut
        default_index = self.categorie_input.findText("Autre")
        if default_index >= 0:
            self.categorie_input.setCurrentIndex(default_index)

        info_layout.addRow("Catégorie:", self.categorie_input)

        # Prix au kg - remplacé par un QLineEdit avec validateur
        prix_container = QWidget()
        prix_layout = QHBoxLayout(prix_container)
        prix_layout.setContentsMargins(0, 0, 0, 0)
        prix_layout.setSpacing(5)

        self.prix_kg_input = QLineEdit()
        self.prix_kg_input.setPlaceholderText("0.00")
        # Validateur pour n'accepter que des nombres décimaux positifs
        validator = QDoubleValidator(0, 9999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.prix_kg_input.setValidator(validator)
        # Largeur fixe pour le champ de prix
        self.prix_kg_input.setFixedWidth(100)

        prix_layout.addWidget(self.prix_kg_input)

        # Unité €/kg affichée en dehors du champ
        prix_layout.addWidget(QLabel("€/kg"))
        prix_layout.addStretch()  # Espace flexible

        info_layout.addRow("Prix au kg:", prix_container)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # ---------- Groupe Valeurs nutritionnelles ----------
        nutrition_group = QGroupBox("Valeurs nutritionnelles (pour 100g)")
        nutrition_layout = QGridLayout()

        # Disposition en grille pour une meilleure utilisation de l'espace
        self.calories_input = self._create_nutrition_spinbox(0, 1000, " kcal", 0)
        self.proteines_input = self._create_nutrition_spinbox(0, 100, " g", 1)
        self.glucides_input = self._create_nutrition_spinbox(0, 100, " g", 1)
        self.lipides_input = self._create_nutrition_spinbox(0, 100, " g", 1)
        self.fibres_input = self._create_nutrition_spinbox(0, 100, " g", 1)

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

        # Étirer le layout pour remplir l'espace
        main_layout.addStretch()

        # Boutons
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

        # Si on modifie un aliment existant, remplir les champs
        if self.aliment:
            self.fill_data_from_aliment()

    def _create_nutrition_spinbox(self, min_val, max_val, suffix, decimals):
        """Crée un spinbox formaté pour les valeurs nutritionnelles"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSuffix(suffix)
        spinbox.setDecimals(decimals)
        spinbox.setMinimumWidth(100)
        spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        spinbox.setStyleSheet(
            """
            QDoubleSpinBox {
                padding-right: 5px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """
        )
        return spinbox

    def fill_data_from_aliment(self):
        """Remplit les champs avec les données de l'aliment à modifier"""
        self.nom_input.setText(self.aliment["nom"])
        self.marque_input.setText(self.aliment["marque"] or "")
        self.magasin_input.setText(self.aliment["magasin"] or "")

        # Gestion spéciale pour la catégorie (ComboBox)
        categorie = self.aliment["categorie"] or ""
        index = self.categorie_input.findText(categorie)
        if index >= 0:
            self.categorie_input.setCurrentIndex(index)
        else:
            # Si la catégorie n'existe pas dans la liste, l'ajouter
            if categorie:
                self.categorie_input.addItem(categorie)
                self.categorie_input.setCurrentText(categorie)

        # Gestion spéciale pour le prix (QLineEdit)
        if self.aliment["prix_kg"]:
            self.prix_kg_input.setText(f"{self.aliment['prix_kg']:.2f}")
        else:
            self.prix_kg_input.setText("")

        self.calories_input.setValue(self.aliment["calories"] or 0)
        self.proteines_input.setValue(self.aliment["proteines"] or 0)
        self.glucides_input.setValue(self.aliment["glucides"] or 0)
        self.lipides_input.setValue(self.aliment["lipides"] or 0)
        self.fibres_input.setValue(self.aliment["fibres"] or 0)

    def accept(self):
        """Vérification des données avant d'accepter le dialogue"""
        # Vérifier que tous les champs obligatoires sont remplis
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

        # Si tout est valide, accepter le dialogue
        super().accept()

    def get_data(self):
        """Retourne les données saisies sous forme de dictionnaire"""
        # Conversion spéciale pour le prix (texte -> float)
        prix_text = self.prix_kg_input.text().strip()

        try:
            prix_kg = float(prix_text.replace(",", ".")) if prix_text else None
        except ValueError:
            prix_kg = None

        return {
            "nom": self.nom_input.text().strip(),
            "marque": self.marque_input.text().strip(),  # Plus de 'or None' car obligatoire
            "magasin": self.magasin_input.text().strip(),  # Plus de 'or None' car obligatoire
            "categorie": self.categorie_input.currentText().strip(),
            "calories": self.calories_input.value(),
            "proteines": self.proteines_input.value(),
            "glucides": self.glucides_input.value(),
            "lipides": self.lipides_input.value(),
            "fibres": self.fibres_input.value(),
            "prix_kg": prix_kg,
        }
