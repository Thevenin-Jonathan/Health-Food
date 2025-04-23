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
    QWidget,
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
        self.setMinimumHeight(800)  # Plus grand pour accueillir l'aperçu

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

        # Aperçu avant/après - Version améliorée avec le même style que l'AlimentComposeDialog
        preview_layout = QVBoxLayout()

        # Titre de la section avec style amélioré
        preview_title = QLabel("Impact nutritionnel sur l'aliment composé")
        preview_title.setProperty("class", "nutrition-title")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_title)

        # Cadre nutritionnel stylisé
        nutrition_frame = QFrame()
        nutrition_frame.setObjectName("nutrition-frame")  # Pour cibler avec QSS
        nutrition_frame.setProperty("class", "nutrition-summary")  # Style existant
        nutrition_frame.setFrameShape(QFrame.StyledPanel)
        nutrition_frame.setMaximumWidth(360)  # Limite la largeur totale du cadre

        nutrition_layout = QGridLayout(nutrition_frame)
        nutrition_layout.setContentsMargins(15, 15, 15, 15)
        nutrition_layout.setVerticalSpacing(8)
        nutrition_layout.setHorizontalSpacing(15)

        # En-tête stylisé
        header_label = QLabel("Valeurs avant / après")
        header_label.setProperty("class", "nutrition-subtitle")
        header_label.setAlignment(Qt.AlignCenter)
        nutrition_layout.addWidget(header_label, 0, 0, 1, 3)

        # Ligne de séparation sous le titre
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #d1e3fa; margin: 5px 0px;")
        separator.setMaximumHeight(2)
        nutrition_layout.addWidget(separator, 1, 0, 1, 3)

        # Structure des données nutritionnelles à afficher
        nutrition_data = [
            ("🔥", "Calories:", "calories", "kcal", False),
            ("🥩", "Protéines:", "proteines", "g", True),
            ("🍞", "Glucides:", "glucides", "g", True),
            ("🥑", "Lipides:", "lipides", "g", True),
            ("🥦", "Fibres:", "fibres", "g", True),
        ]

        # Créer un widget conteneur avec taille fixe pour chaque ligne
        for row, (icon_text, label_text, attr_name, unit, decimal) in enumerate(
            nutrition_data, 2
        ):
            # Container pour cette ligne
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)

            # Icône
            icon_label = QLabel(icon_text)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedWidth(30)
            row_layout.addWidget(icon_label)

            # Nom du nutriment
            name_label = QLabel(label_text)
            name_label.setProperty("class", "nutrition-subtitle")
            name_label.setFixedWidth(80)
            row_layout.addWidget(name_label)

            # Layout pour les valeurs actuelles et futures
            values_widget = QWidget()
            values_layout = QHBoxLayout(values_widget)
            values_layout.setContentsMargins(0, 0, 0, 0)
            values_layout.setSpacing(5)

            # Valeur actuelle
            format_str = "{:.1f}" if decimal else "{:.0f}"
            current_val = QLabel(
                format_str.format(self.current_values[attr_name]) + f" {unit}"
            )
            current_val.setProperty("class", "nutrition-value")
            if attr_name != "fibres":  # Ne pas appliquer de couleur aux fibres
                current_val.setProperty("type", attr_name)
            current_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            current_val.setFixedWidth(70)
            setattr(self, f"current_{attr_name}", current_val)
            values_layout.addWidget(current_val)

            # Séparateur
            arrow_label = QLabel("→")
            arrow_label.setAlignment(Qt.AlignCenter)
            arrow_label.setFixedWidth(20)
            arrow_label.setStyleSheet("color: #777;")
            values_layout.addWidget(arrow_label)

            # Nouvelle valeur
            new_val = QLabel(
                format_str.format(self.current_values[attr_name]) + f" {unit}"
            )
            new_val.setProperty("class", "result-value-highlight")
            if attr_name != "fibres":  # Ne pas appliquer de couleur aux fibres
                new_val.setProperty("type", attr_name)
            new_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            new_val.setFixedWidth(70)
            setattr(self, f"new_{attr_name}", new_val)
            values_layout.addWidget(new_val)

            # Ajouter le layout des valeurs au layout de la ligne
            row_layout.addWidget(values_widget)

            # Ajouter la ligne complète au layout principal
            nutrition_layout.addWidget(row_widget, row, 0, 1, 3)

        # Centrer le cadre nutritionnel dans son conteneur
        nutrition_container = QHBoxLayout()
        nutrition_container.addStretch()
        nutrition_container.addWidget(nutrition_frame)
        nutrition_container.addStretch()

        preview_layout.addLayout(nutrition_container)
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
                "format": "{:.0f}",
            },
            "proteines": {
                "current": self.current_values["proteines"],
                "added": self.selected_aliment["proteines"] * quantity_factor,
                "format": "{:.1f}",
            },
            "glucides": {
                "current": self.current_values["glucides"],
                "added": self.selected_aliment["glucides"] * quantity_factor,
                "format": "{:.1f}",
            },
            "lipides": {
                "current": self.current_values["lipides"],
                "added": self.selected_aliment["lipides"] * quantity_factor,
                "format": "{:.1f}",
            },
            "fibres": {
                "current": self.current_values["fibres"],
                "added": self.selected_aliment.get("fibres", 0) * quantity_factor,
                "format": "{:.1f}",
            },
        }

        # Les unités correspondant à chaque nutriment
        units = {
            "calories": "kcal",
            "proteines": "g",
            "glucides": "g",
            "lipides": "g",
            "fibres": "g",
        }

        # Mettre à jour les labels
        for attr, values in nutrition_values.items():
            current = values["current"]
            added = values["added"]
            new_value = current + added
            format_str = values["format"]
            unit = units[attr]

            # Mise à jour des labels avec le format et l'unité
            getattr(self, f"current_{attr}").setText(
                f"{format_str.format(current)} {unit}"
            )
            getattr(self, f"new_{attr}").setText(
                f"{format_str.format(new_value)} {unit}"
            )

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
            ("calories", "{:.0f}", "kcal"),
            ("proteines", "{:.1f}", "g"),
            ("glucides", "{:.1f}", "g"),
            ("lipides", "{:.1f}", "g"),
            ("fibres", "{:.1f}", "g"),
        ]

        for attr, format_str, unit in nutrition_attrs:
            current_value = self.current_values[attr]

            # Mettre à jour les labels avec les valeurs actuelles
            getattr(self, f"current_{attr}").setText(
                f"{format_str.format(current_value)} {unit}"
            )
            getattr(self, f"new_{attr}").setText(
                f"{format_str.format(current_value)} {unit}"
            )

    def get_data(self):
        """Retourne l'ID de l'aliment et la quantité sélectionnés"""
        return (self.selected_aliment_id, self.quantity_spin.value())
