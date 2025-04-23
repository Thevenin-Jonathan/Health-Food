from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal


# Classe pour les items du tableau avec tri numérique correct
class NumericTableItem(QTableWidgetItem):
    def __init__(self, value, text=""):
        super().__init__(text)
        self.setData(Qt.UserRole, float(value) if value is not None else 0.0)
        self.setTextAlignment(Qt.AlignCenter)

    def __lt__(self, other):
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)


class AlimentSimpleSelectionDialog(QDialog):
    """Dialogue pour sélectionner un aliment simple pour un ingrédient d'aliment composé"""

    # Signal pour notifier des changements dans les valeurs nutritionnelles
    nutritionChanged = Signal(
        float, float, float, float, float
    )  # calories, p, g, l, fibres

    def __init__(self, parent=None, db_manager=None, current_values=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un ingrédient")
        self.db_manager = db_manager
        self.selected_aliment_id = None
        self.selected_aliment = None

        # Valeurs nutritionnelles actuelles de l'aliment composé
        self.current_values = current_values or {
            "calories": 0,
            "proteines": 0,
            "glucides": 0,
            "lipides": 0,
            "fibres": 0,
        }

        self.setup_ui()
        self.load_aliments()

        # Connecter le signal de modification de quantité
        self.quantity_spin.valueChanged.connect(self.update_nutrition_preview)

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)  # Plus grand pour accueillir l'aperçu

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # Filtres
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrer par:"))

        # Catégorie
        self.category_filter = QComboBox()
        self.category_filter.addItem("Toutes les catégories", "")
        categories = self.db_manager.get_categories_uniques()
        for cat in categories:
            self.category_filter.addItem(cat, cat)
        self.category_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)

        # Marque
        self.brand_filter = QComboBox()
        self.brand_filter.addItem("Toutes les marques", "")
        brands = self.db_manager.get_marques_uniques()
        for brand in brands:
            if brand:  # Éviter les valeurs null/empty
                self.brand_filter.addItem(brand, brand)
        self.brand_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.brand_filter)

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        main_layout.addLayout(filter_layout)

        # Tableau des aliments
        self.aliments_table = QTableWidget()
        self.aliments_table.setSortingEnabled(True)
        self.aliments_table.setColumnCount(5)
        self.aliments_table.setHorizontalHeaderLabels(
            ["Nom", "Marque", "Calories", "Protéines", "Catégorie"]
        )
        header = self.aliments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nom
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Marque
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Calories
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Protéines
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Catégorie

        self.aliments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.aliments_table.setSelectionMode(QTableWidget.SingleSelection)
        self.aliments_table.itemSelectionChanged.connect(self.update_selection)
        self.aliments_table.verticalHeader().setVisible(
            False
        )  # Masquer les numéros de ligne

        # Double-clic pour sélection rapide
        self.aliments_table.itemDoubleClicked.connect(self.accept)

        main_layout.addWidget(self.aliments_table, 1)  # Donner tout l'espace disponible

        # Séparateur horizontal
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Aperçu avant/après - Version améliorée avec styles existants
        preview_layout = QVBoxLayout()

        # Titre de l'aperçu avec style
        preview_title = QLabel("Impact nutritionnel sur l'aliment composé")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_title.setProperty(
            "class", "nutrition-title"
        )  # Utilisation d'une classe existante
        preview_layout.addWidget(preview_title)

        # Cadre stylisé pour l'aperçu nutritionnel utilisant les styles existants
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setFrameShadow(QFrame.Raised)
        preview_frame.setObjectName(
            "nutrition-frame"
        )  # Utilisation d'un style existant
        preview_frame.setProperty(
            "class", "nutrition-summary"
        )  # Utilisation d'une classe existante

        # Layout pour le cadre
        frame_layout = QGridLayout(preview_frame)
        frame_layout.setSpacing(6)
        frame_layout.setContentsMargins(10, 10, 10, 10)

        # En-têtes stylisés
        headers = ["", "Actuel", "+", "Ajout", "=", "Nouveau"]
        for i, text in enumerate(headers):
            header = QLabel(text)
            header.setProperty("class", "bold")  # Utilisation d'une classe existante
            header.setAlignment(Qt.AlignCenter)
            if i == 0:
                header.setAlignment(Qt.AlignLeft)
            frame_layout.addWidget(header, 0, i)

        # Ligne de séparation sous les en-têtes
        header_line = QFrame()
        header_line.setFrameShape(QFrame.HLine)
        header_line.setFrameShadow(QFrame.Sunken)
        frame_layout.addWidget(header_line, 1, 0, 1, 6)

        # Données nutritionnelles avec des styles cohérents par type de nutriment
        nutrition_data = [
            ("Calories:", "calories", "kcal", False),
            ("Protéines:", "proteines", "g", True),
            ("Glucides:", "glucides", "g", True),
            ("Lipides:", "lipides", "g", True),
            ("Fibres:", "fibres", "g", True),
        ]

        for row, (label_text, attr, unit, decimal) in enumerate(nutrition_data, 2):
            # Label du nutriment
            label = QLabel(label_text)
            label.setProperty(
                "class", "nutrition-subtitle"
            )  # Utilisation d'une classe existante
            frame_layout.addWidget(label, row, 0)

            # Valeur actuelle
            format_str = "{:.1f}" if decimal else "{:.0f}"
            current_val = QLabel(
                f"{format_str.format(self.current_values[attr])} {unit}"
            )
            current_val.setAlignment(Qt.AlignCenter)
            current_val.setProperty(
                "type", attr
            )  # Pour que les couleurs spécifiques s'appliquent
            current_val.setProperty("class", "nutrition-value")  # Style existant
            setattr(self, f"current_{attr}", current_val)
            frame_layout.addWidget(current_val, row, 1)

            # Symbole plus
            plus = QLabel("+")
            plus.setAlignment(Qt.AlignCenter)
            plus.setProperty("class", "hint")  # Style existant pour un texte grisé
            frame_layout.addWidget(plus, row, 2)

            # Valeur ajoutée - utilise la classe existante mais avec un style spécifique
            added_val = QLabel(f"0 {unit}")
            added_val.setAlignment(Qt.AlignCenter)
            added_val.setProperty("class", "nutrition-value")
            added_val.setProperty(
                "type", attr
            )  # Pour que les couleurs spécifiques s'appliquent
            added_val.setStyleSheet(
                "font-weight: bold; color: #0078d7;"
            )  # Style spécifique en bleu
            setattr(self, f"added_{attr}", added_val)
            frame_layout.addWidget(added_val, row, 3)

            # Symbole égal
            equal = QLabel("=")
            equal.setAlignment(Qt.AlignCenter)
            equal.setProperty("class", "hint")  # Style existant pour un texte grisé
            frame_layout.addWidget(equal, row, 4)

            # Nouvelle valeur - utilisez la classe pour les valeurs mises en évidence
            new_val = QLabel(f"{format_str.format(self.current_values[attr])} {unit}")
            new_val.setAlignment(Qt.AlignCenter)
            new_val.setProperty(
                "class", "result-value-highlight"
            )  # Style existant pour mettre en évidence
            new_val.setProperty(
                "type", attr
            )  # Pour que les couleurs spécifiques s'appliquent
            setattr(self, f"new_{attr}", new_val)
            frame_layout.addWidget(new_val, row, 5)

        preview_layout.addWidget(preview_frame)
        main_layout.addLayout(preview_layout)

        # Séparateur horizontal
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator2)

        # Quantité
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantité:"))

        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1000)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setProperty("class", "spin-box-vertical")  # Classe existante
        self.quantity_spin.setSuffix(" g")
        quantity_layout.addWidget(self.quantity_spin)
        quantity_layout.addStretch()

        main_layout.addLayout(quantity_layout)

        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("Ajouter")
        self.add_btn.setDefault(True)
        self.add_btn.setEnabled(False)  # Désactivé jusqu'à sélection
        self.add_btn.clicked.connect(self.accept)

        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.add_btn)

        main_layout.addLayout(buttons_layout)

    def load_aliments(self):
        """Charge tous les aliments dans le tableau"""
        self.apply_filters()

    def apply_filters(self):
        """Applique les filtres pour les aliments"""
        category = self.category_filter.currentData()
        brand = self.brand_filter.currentData()
        search = self.search_input.text().strip()

        aliments = self.db_manager.get_aliments(
            categorie=category if category else None,
            marque=brand if brand else None,
            recherche=search if search else None,
            sort_column="nom",
        )

        # Désactiver le tri pendant le chargement
        self.aliments_table.setSortingEnabled(False)

        self.aliments_table.setRowCount(0)
        self.aliments_table.setRowCount(len(aliments))

        for i, aliment in enumerate(aliments):
            # Nom
            nom_item = QTableWidgetItem(aliment["nom"])
            self.aliments_table.setItem(i, 0, nom_item)

            # Marque
            marque_item = QTableWidgetItem(aliment.get("marque", ""))
            self.aliments_table.setItem(i, 1, marque_item)

            # Calories
            calories_item = NumericTableItem(
                aliment["calories"], f"{aliment['calories']:.0f}"
            )
            self.aliments_table.setItem(i, 2, calories_item)

            # Protéines
            proteines_item = NumericTableItem(
                aliment["proteines"], f"{aliment['proteines']:.1f}"
            )
            self.aliments_table.setItem(i, 3, proteines_item)

            # Catégorie
            categorie_item = QTableWidgetItem(aliment.get("categorie", ""))
            self.aliments_table.setItem(i, 4, categorie_item)

            # Stocker l'ID comme donnée utilisateur dans toutes les cellules
            for col in range(5):
                self.aliments_table.item(i, col).setData(Qt.UserRole + 1, aliment["id"])

        # Réactiver le tri
        self.aliments_table.setSortingEnabled(True)

    def update_selection(self):
        """Met à jour l'aliment sélectionné"""
        selected_items = self.aliments_table.selectedItems()
        if selected_items:
            # Récupérer l'ID à partir de la donnée utilisateur
            self.selected_aliment_id = selected_items[0].data(Qt.UserRole + 1)
            self.add_btn.setEnabled(True)

            # Récupérer les informations complètes de l'aliment
            self.selected_aliment = self.db_manager.get_aliment(
                self.selected_aliment_id
            )

            # Mettre à jour l'aperçu des valeurs nutritionnelles
            self.update_nutrition_preview()
        else:
            self.selected_aliment_id = None
            self.selected_aliment = None
            self.add_btn.setEnabled(False)

            # Réinitialiser l'aperçu
            self.reset_nutrition_preview()

    def update_nutrition_preview(self):
        """Met à jour l'aperçu des valeurs nutritionnelles en fonction de l'aliment sélectionné"""
        if not self.selected_aliment:
            self.reset_nutrition_preview()
            return

        # Calculer les valeurs nutritionnelles ajoutées en fonction de la quantité
        quantity_factor = self.quantity_spin.value() / 100.0  # Pour 100g

        # Structure de données pour simplifier la mise à jour
        nutrition_values = {
            "calories": {
                "current": self.current_values["calories"],
                "added": self.selected_aliment["calories"] * quantity_factor,
                "format": "{:.0f} kcal",
            },
            "proteines": {
                "current": self.current_values["proteines"],
                "added": self.selected_aliment["proteines"] * quantity_factor,
                "format": "{:.1f} g",
            },
            "glucides": {
                "current": self.current_values["glucides"],
                "added": self.selected_aliment["glucides"] * quantity_factor,
                "format": "{:.1f} g",
            },
            "lipides": {
                "current": self.current_values["lipides"],
                "added": self.selected_aliment["lipides"] * quantity_factor,
                "format": "{:.1f} g",
            },
            "fibres": {
                "current": self.current_values["fibres"],
                "added": self.selected_aliment.get("fibres", 0) * quantity_factor,
                "format": "{:.1f} g",
            },
        }

        # Mettre à jour tous les labels
        for attr, values in nutrition_values.items():
            # Calculer la nouvelle valeur
            new_value = values["current"] + values["added"]

            # Mettre à jour les labels
            getattr(self, f"added_{attr}").setText(
                values["format"].format(values["added"])
            )
            getattr(self, f"new_{attr}").setText(values["format"].format(new_value))

        # Émettre le signal avec les valeurs ajoutées
        self.nutritionChanged.emit(
            nutrition_values["calories"]["added"],
            nutrition_values["proteines"]["added"],
            nutrition_values["glucides"]["added"],
            nutrition_values["lipides"]["added"],
            nutrition_values["fibres"]["added"],
        )

    def reset_nutrition_preview(self):
        """Réinitialise l'aperçu des valeurs nutritionnelles"""
        # Structure pour simplifier la réinitialisation
        nutrition_attrs = [
            ("calories", "{:.0f} kcal"),
            ("proteines", "{:.1f} g"),
            ("glucides", "{:.1f} g"),
            ("lipides", "{:.1f} g"),
            ("fibres", "{:.1f} g"),
        ]

        for attr, format_str in nutrition_attrs:
            current_value = self.current_values[attr]

            # Mettre à jour les labels
            getattr(self, f"current_{attr}").setText(format_str.format(current_value))
            getattr(self, f"added_{attr}").setText(format_str.format(0))
            getattr(self, f"new_{attr}").setText(format_str.format(current_value))

    def get_data(self):
        """Retourne l'ID de l'aliment et la quantité sélectionnés"""
        return (self.selected_aliment_id, self.quantity_spin.value())
