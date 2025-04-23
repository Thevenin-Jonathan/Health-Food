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
    QTabWidget,
    QWidget,
    QFrame,
    QGridLayout,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal
from src.utils import AutoSelectDoubleSpinBox


# Classe pour les items du tableau avec tri numérique correct
class NumericTableItem(QTableWidgetItem):
    def __init__(self, value, text=""):
        super().__init__(text)
        self.setData(Qt.UserRole, float(value) if value is not None else 0.0)
        self.setTextAlignment(Qt.AlignCenter)

    def __lt__(self, other):
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)


class AlimentRepasDialog(QDialog):
    """Dialogue pour ajouter un aliment ou un aliment composé à un repas"""

    # Signal pour notifier des changements dans les valeurs nutritionnelles
    nutritionChanged = Signal(
        float, float, float, float, float
    )  # calories, p, g, l, fibres

    def __init__(
        self,
        parent=None,
        db_manager=None,
        semaine_id=None,
        jour=None,
        objectifs=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Ajouter à un repas")
        self.db_manager = db_manager
        self.semaine_id = semaine_id
        self.jour = jour
        self.selected_aliment_id = None
        self.selected_aliment_compose_id = None
        self.mode_aliment_compose = False

        # Récupérer les données nutritionnelles de la journée entière
        self.valeurs_actuelles = (
            self.calculer_valeurs_journee()
            if semaine_id and jour
            else {
                "calories": 0,
                "proteines": 0,
                "glucides": 0,
                "lipides": 0,
                "fibres": 0,
            }
        )

        # Objectifs nutritionnels
        self.objectifs = objectifs or self.charger_objectifs_utilisateur()

        # Seuils pour la coloration des barres de progression
        self.THRESHOLD_OVER = 1.05  # Plus de 105%
        self.THRESHOLD_GOOD_UPPER = 1.05  # Limite supérieure pour "bon"
        self.THRESHOLD_GOOD_LOWER = 0.95  # Limite inférieure pour "bon"
        self.THRESHOLD_LOW = 0.5  # Seuil pour "bas"

        self.setup_ui()

        # Connecter le signal de mise à jour nutritionnelle
        self.nutritionChanged.connect(self.update_nutrition_preview)

    def calculer_valeurs_journee(self):
        """Calcule les valeurs nutritionnelles totales pour la journée actuelle"""
        if not self.semaine_id or not self.jour:
            return {
                "calories": 0,
                "proteines": 0,
                "glucides": 0,
                "lipides": 0,
                "fibres": 0,
            }

        # Récupérer tous les repas de la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)

        # Si le jour n'existe pas dans les données
        if self.jour not in repas_semaine:
            return {
                "calories": 0,
                "proteines": 0,
                "glucides": 0,
                "lipides": 0,
                "fibres": 0,
            }

        # Récupérer les repas du jour spécifié
        repas_jour = repas_semaine[self.jour]

        # Calculer les totaux pour la journée
        total_calories = sum(repas.get("total_calories", 0) for repas in repas_jour)
        total_proteines = sum(repas.get("total_proteines", 0) for repas in repas_jour)
        total_glucides = sum(repas.get("total_glucides", 0) for repas in repas_jour)
        total_lipides = sum(repas.get("total_lipides", 0) for repas in repas_jour)
        total_fibres = 0  # Les fibres ne sont peut-être pas disponibles partout

        return {
            "calories": total_calories,
            "proteines": total_proteines,
            "glucides": total_glucides,
            "lipides": total_lipides,
            "fibres": total_fibres,
        }

    def charger_objectifs_utilisateur(self):
        """Récupère les objectifs nutritionnels de l'utilisateur"""
        try:
            user_data = self.db_manager.get_utilisateur()
            return {
                "calories": max(1, user_data.get("objectif_calories", 2500)),
                "proteines": max(1, user_data.get("objectif_proteines", 180)),
                "glucides": max(1, user_data.get("objectif_glucides", 250)),
                "lipides": max(1, user_data.get("objectif_lipides", 70)),
            }
        except Exception as e:
            print(f"Error loading user objectives: {e}")
            # Retourner des valeurs par défaut en cas d'erreur
            return {
                "calories": 2500,
                "proteines": 180,
                "glucides": 250,
                "lipides": 70,
            }

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # TabWidget pour séparer aliments simples et composés
        self.tab_widget = QTabWidget()

        # Tab pour les aliments simples
        self.simple_tab = QWidget()
        simple_layout = QVBoxLayout(self.simple_tab)
        simple_layout.setContentsMargins(0, 8, 0, 8)
        simple_layout.setSpacing(8)

        # Filtres pour aliments simples
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

        simple_layout.addLayout(filter_layout)

        # Tableau des aliments - Masquer les numéros de ligne
        self.aliments_table = QTableWidget()
        self.aliments_table.setSortingEnabled(True)
        self.aliments_table.setColumnCount(4)  # Réduction des colonnes
        self.aliments_table.setHorizontalHeaderLabels(
            ["Nom", "Marque", "Calories", "Protéines"]
        )
        header = self.aliments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nom
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Marque
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Calories
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Protéines

        # Masquer les numéros de ligne
        self.aliments_table.verticalHeader().setVisible(False)

        self.aliments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.aliments_table.setSelectionMode(QTableWidget.SingleSelection)
        self.aliments_table.itemSelectionChanged.connect(self.update_aliment_selection)

        simple_layout.addWidget(self.aliments_table)

        # Tab pour les aliments composés - Masquer les numéros de ligne
        self.compose_tab = QWidget()
        compose_layout = QVBoxLayout(self.compose_tab)
        compose_layout.setContentsMargins(0, 8, 0, 8)
        compose_layout.setSpacing(8)

        # Filtre par catégorie pour aliments composés
        comp_filter_layout = QHBoxLayout()
        comp_filter_layout.addWidget(QLabel("Catégorie:"))

        self.comp_category_filter = QComboBox()
        self.comp_category_filter.addItem("Toutes les catégories", "")
        comp_categories = self.db_manager.get_categories_aliments_composes()
        for cat in comp_categories:
            self.comp_category_filter.addItem(cat, cat)
        self.comp_category_filter.currentIndexChanged.connect(
            self.apply_compose_filters
        )
        comp_filter_layout.addWidget(self.comp_category_filter)

        # Recherche pour aliments composés
        self.comp_search_input = QLineEdit()
        self.comp_search_input.setPlaceholderText("Rechercher...")
        self.comp_search_input.textChanged.connect(self.apply_compose_filters)
        comp_filter_layout.addWidget(self.comp_search_input)

        # Bouton pour gérer les aliments composés
        self.btn_manage_compose = QPushButton("Gérer les aliments composés")
        self.btn_manage_compose.clicked.connect(self.open_compose_manager)
        comp_filter_layout.addWidget(self.btn_manage_compose)

        compose_layout.addLayout(comp_filter_layout)

        # Tableau des aliments composés - Masquer les numéros de ligne
        self.compose_table = QTableWidget()
        self.compose_table.setSortingEnabled(True)
        self.compose_table.setColumnCount(3)  # Réduction des colonnes
        self.compose_table.setHorizontalHeaderLabels(["Nom", "Catégorie", "Calories"])
        header = self.compose_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nom
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Catégorie
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Calories

        # Masquer les numéros de ligne
        self.compose_table.verticalHeader().setVisible(False)

        self.compose_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.compose_table.setSelectionMode(QTableWidget.SingleSelection)
        self.compose_table.itemSelectionChanged.connect(self.update_compose_selection)

        compose_layout.addWidget(self.compose_table)

        # Ajouter les tabs
        self.tab_widget.addTab(self.simple_tab, "Aliments simples")
        self.tab_widget.addTab(self.compose_tab, "Aliments composés (mélanges)")

        # Connecter le changement de tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        # Section inférieure avec grille: quantité + infos nutritionnelles
        bottom_widget = QWidget()
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)

        # Colonne 1: Quantité et détails aliment
        col1_widget = QWidget()
        col1_layout = QVBoxLayout(col1_widget)
        col1_layout.setContentsMargins(0, 0, 0, 0)
        col1_layout.setSpacing(8)

        # Section pour la quantité avec design amélioré
        quant_widget = QWidget()
        quant_widget.setStyleSheet(
            """
            QWidget {
                background-color: #f5f5f5;
                border-radius: 6px;
            }
            QLabel {
                font-weight: bold;
            }
            QDoubleSpinBox {
                font-size: 16px;
                padding: 4px;
                min-width: 80px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """
        )
        quant_layout = QHBoxLayout(quant_widget)
        quant_layout.setContentsMargins(12, 8, 12, 8)

        quant_label = QLabel("Quantité:")
        quant_layout.addWidget(quant_label)

        self.quantite_spin = AutoSelectDoubleSpinBox()
        self.quantite_spin.setMinimum(1)
        self.quantite_spin.setMaximum(1000)
        self.quantite_spin.setValue(100)
        self.quantite_spin.setSuffix(" g")
        self.quantite_spin.valueChanged.connect(self.update_details)
        quant_layout.addWidget(self.quantite_spin)

        col1_layout.addWidget(quant_widget)

        # Détails de l'aliment sélectionné dans un cadre stylisé
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #e9ecef;
                padding: 0px;
            }
        """
        )

        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(8, 8, 8, 8)

        self.details_label = QLabel()
        self.details_label.setTextFormat(Qt.RichText)
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)

        col1_layout.addWidget(details_frame, 1)  # 1 = stretch factor

        # Colonne 2: Aperçu des valeurs nutritionnelles de la journée
        col2_widget = QFrame()
        col2_widget.setFrameShape(QFrame.StyledPanel)
        col2_widget.setStyleSheet(
            """
            QFrame {
                background-color: #f0f4f8;
                border-radius: 6px;
                border: 1px solid #d1e3fa;
            }
            QLabel.title {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding-bottom: 5px;
                border-bottom: 1px solid #d1e3fa;
            }
            QLabel.subtitle {
                font-weight: bold;
                color: #34495e;
                margin-top: 5px;
            }
        """
        )

        col2_layout = QVBoxLayout(col2_widget)
        col2_layout.setSpacing(8)

        # Titre
        title_label = QLabel("Aperçu des valeurs nutritionnelles")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        col2_layout.addWidget(title_label)

        # Sous-titre "Actuellement"
        current_label = QLabel("Actuellement")
        current_label.setProperty("class", "subtitle")
        col2_layout.addWidget(current_label)

        # Valeurs actuelles avec barres de progression
        self.progress_layout = QGridLayout()
        self.progress_layout.setColumnStretch(1, 1)

        # Calories
        self.progress_layout.addWidget(QLabel("Calories:"), 0, 0)
        self.cal_progress = QProgressBar()
        self.cal_progress.setProperty("class", "calories")
        self.cal_progress.setTextVisible(True)
        self.progress_layout.addWidget(self.cal_progress, 0, 1)
        self.cal_value = QLabel()
        self.cal_value.setAlignment(Qt.AlignRight)
        self.progress_layout.addWidget(self.cal_value, 0, 2)

        # Protéines
        self.progress_layout.addWidget(QLabel("Protéines:"), 1, 0)
        self.prot_progress = QProgressBar()
        self.prot_progress.setProperty("class", "proteines")
        self.prot_progress.setTextVisible(True)
        self.progress_layout.addWidget(self.prot_progress, 1, 1)
        self.prot_value = QLabel()
        self.prot_value.setAlignment(Qt.AlignRight)
        self.progress_layout.addWidget(self.prot_value, 1, 2)

        # Glucides
        self.progress_layout.addWidget(QLabel("Glucides:"), 2, 0)
        self.gluc_progress = QProgressBar()
        self.gluc_progress.setProperty("class", "glucides")
        self.gluc_progress.setTextVisible(True)
        self.progress_layout.addWidget(self.gluc_progress, 2, 1)
        self.gluc_value = QLabel()
        self.gluc_value.setAlignment(Qt.AlignRight)
        self.progress_layout.addWidget(self.gluc_value, 2, 2)

        # Lipides
        self.progress_layout.addWidget(QLabel("Lipides:"), 3, 0)
        self.lip_progress = QProgressBar()
        self.lip_progress.setProperty("class", "lipides")
        self.lip_progress.setTextVisible(True)
        self.progress_layout.addWidget(self.lip_progress, 3, 1)
        self.lip_value = QLabel()
        self.lip_value.setAlignment(Qt.AlignRight)
        self.progress_layout.addWidget(self.lip_value, 3, 2)

        col2_layout.addLayout(self.progress_layout)

        # Sous-titre "Après ajout"
        after_label = QLabel("Après ajout de cet aliment")
        after_label.setProperty("class", "subtitle")
        col2_layout.addWidget(after_label)

        # Valeurs après ajout
        self.after_layout = QGridLayout()
        self.after_layout.setColumnStretch(1, 1)

        # Calories après
        self.after_layout.addWidget(QLabel("Calories:"), 0, 0)
        self.cal_after_progress = QProgressBar()
        self.cal_after_progress.setProperty("class", "calories")
        self.cal_after_progress.setTextVisible(True)
        self.after_layout.addWidget(self.cal_after_progress, 0, 1)
        self.cal_after_value = QLabel()
        self.cal_after_value.setAlignment(Qt.AlignRight)
        self.after_layout.addWidget(self.cal_after_value, 0, 2)

        # Protéines après
        self.after_layout.addWidget(QLabel("Protéines:"), 1, 0)
        self.prot_after_progress = QProgressBar()
        self.prot_after_progress.setProperty("class", "proteines")
        self.prot_after_progress.setTextVisible(True)
        self.after_layout.addWidget(self.prot_after_progress, 1, 1)
        self.prot_after_value = QLabel()
        self.prot_after_value.setAlignment(Qt.AlignRight)
        self.after_layout.addWidget(self.prot_after_value, 1, 2)

        # Glucides après
        self.after_layout.addWidget(QLabel("Glucides:"), 2, 0)
        self.gluc_after_progress = QProgressBar()
        self.gluc_after_progress.setProperty("class", "glucides")
        self.gluc_after_progress.setTextVisible(True)
        self.after_layout.addWidget(self.gluc_after_progress, 2, 1)
        self.gluc_after_value = QLabel()
        self.gluc_after_value.setAlignment(Qt.AlignRight)
        self.after_layout.addWidget(self.gluc_after_value, 2, 2)

        # Lipides après
        self.after_layout.addWidget(QLabel("Lipides:"), 3, 0)
        self.lip_after_progress = QProgressBar()
        self.lip_after_progress.setProperty("class", "lipides")
        self.lip_after_progress.setTextVisible(True)
        self.after_layout.addWidget(self.lip_after_progress, 3, 1)
        self.lip_after_value = QLabel()
        self.lip_after_value.setAlignment(Qt.AlignRight)
        self.after_layout.addWidget(self.lip_after_value, 3, 2)

        col2_layout.addLayout(self.after_layout)
        col2_layout.addStretch()

        # Ajouter les colonnes au layout inférieur
        bottom_layout.addWidget(col1_widget, 0, 0)
        bottom_layout.addWidget(col2_widget, 0, 1)

        main_layout.addWidget(bottom_widget)

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

        # Initialiser l'affichage des valeurs nutritionnelles
        self.init_nutrition_preview()

        # Charger les aliments
        self.load_aliments()
        self.load_aliments_composes()

    def on_tab_changed(self, index):
        """Gère le changement d'onglet"""
        self.mode_aliment_compose = index == 1  # 1 = tab des aliments composés
        self.add_btn.setEnabled(False)

        # Mettre à jour les détails selon l'onglet actif
        if self.mode_aliment_compose:
            self.update_compose_details()
        else:
            self.update_aliment_details()

    def load_aliments(self):
        """Charge tous les aliments dans le tableau"""
        aliments = self.db_manager.get_aliments(sort_column="nom")

        # Désactiver le tri pendant le chargement
        self.aliments_table.setSortingEnabled(False)
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

            # Stocker l'ID comme donnée utilisateur dans toutes les cellules
            for col in range(4):
                self.aliments_table.item(i, col).setData(Qt.UserRole + 1, aliment["id"])

        # Réactiver le tri
        self.aliments_table.setSortingEnabled(True)

    def load_aliments_composes(self):
        """Charge les aliments composés dans le tableau"""
        aliments = self.db_manager.get_aliments_composes()

        # Désactiver le tri pendant le chargement
        self.compose_table.setSortingEnabled(False)
        self.compose_table.setRowCount(len(aliments))

        for i, aliment in enumerate(aliments):
            # Nom
            nom_item = QTableWidgetItem(aliment["nom"])
            self.compose_table.setItem(i, 0, nom_item)

            # Catégorie
            categorie_item = QTableWidgetItem(aliment.get("categorie", ""))
            self.compose_table.setItem(i, 1, categorie_item)

            # Calories
            calories_item = NumericTableItem(
                aliment["total_calories"], f"{aliment['total_calories']:.0f}"
            )
            self.compose_table.setItem(i, 2, calories_item)

            # Stocker l'ID comme donnée utilisateur dans toutes les cellules
            for col in range(3):
                self.compose_table.item(i, col).setData(Qt.UserRole + 1, aliment["id"])

        # Réactiver le tri
        self.compose_table.setSortingEnabled(True)

    def apply_filters(self):
        """Applique les filtres pour les aliments simples"""
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

            # Stocker l'ID comme donnée utilisateur
            for col in range(5):
                self.aliments_table.item(i, col).setData(Qt.UserRole + 1, aliment["id"])

        # Réactiver le tri
        self.aliments_table.setSortingEnabled(True)

    def apply_compose_filters(self):
        """Applique les filtres pour les aliments composés"""
        category = self.comp_category_filter.currentData()
        search = self.comp_search_input.text().strip()

        # Récupérer les aliments composés filtrés par catégorie
        aliments = self.db_manager.get_aliments_composes(category)

        # Filtrer manuellement par recherche
        if search:
            search_lower = search.lower()
            aliments = [a for a in aliments if search_lower in a["nom"].lower()]

        # Désactiver le tri pendant le chargement
        self.compose_table.setSortingEnabled(False)

        # Mettre à jour le tableau
        self.compose_table.setRowCount(0)
        self.compose_table.setRowCount(len(aliments))

        for i, aliment in enumerate(aliments):
            # Nom
            nom_item = QTableWidgetItem(aliment["nom"])
            self.compose_table.setItem(i, 0, nom_item)

            # Catégorie
            categorie_item = QTableWidgetItem(aliment.get("categorie", ""))
            self.compose_table.setItem(i, 1, categorie_item)

            # Calories
            calories_item = NumericTableItem(
                aliment["total_calories"], f"{aliment['total_calories']:.0f}"
            )
            self.compose_table.setItem(i, 2, calories_item)

            # Protéines
            proteines_item = NumericTableItem(
                aliment["total_proteines"], f"{aliment['total_proteines']:.1f}"
            )
            self.compose_table.setItem(i, 3, proteines_item)

            # Stocker l'ID comme donnée utilisateur
            for col in range(4):
                self.compose_table.item(i, col).setData(Qt.UserRole + 1, aliment["id"])

        # Réactiver le tri
        self.compose_table.setSortingEnabled(True)

    def update_aliment_selection(self):
        """Met à jour l'aliment sélectionné"""
        selected_items = self.aliments_table.selectedItems()
        if selected_items:
            # Récupérer l'ID à partir de la donnée utilisateur
            self.selected_aliment_id = selected_items[0].data(Qt.UserRole + 1)
            self.selected_aliment_compose_id = None
            self.add_btn.setEnabled(True)

            # Mettre à jour les détails
            self.update_aliment_details()

    def update_compose_selection(self):
        """Met à jour l'aliment composé sélectionné"""
        selected_items = self.compose_table.selectedItems()
        if selected_items:
            # Récupérer l'ID à partir de la donnée utilisateur
            self.selected_aliment_compose_id = selected_items[0].data(Qt.UserRole + 1)
            self.selected_aliment_id = None
            self.add_btn.setEnabled(True)

            # Mettre à jour les détails
            self.update_compose_details()

    def update_details(self):
        """Met à jour les détails en fonction du type d'aliment sélectionné"""
        if self.mode_aliment_compose:
            self.update_compose_details()
        else:
            self.update_aliment_details()

    def update_aliment_details(self):
        """Met à jour les détails de l'aliment sélectionné"""
        if self.selected_aliment_id is None:
            self.details_label.setText("")
            self.nutritionChanged.emit(0, 0, 0, 0, 0)  # Réinitialiser l'aperçu
            return

        aliment = self.db_manager.get_aliment(self.selected_aliment_id)
        if not aliment:
            return

        # Récupérer la quantité sélectionnée
        quantite = self.quantite_spin.value()

        # Calculer les valeurs
        calories = aliment["calories"] * quantite / 100
        proteines = aliment["proteines"] * quantite / 100
        glucides = aliment["glucides"] * quantite / 100
        lipides = aliment["lipides"] * quantite / 100
        fibres = aliment.get("fibres", 0) * quantite / 100

        # Émettre le signal pour mettre à jour l'aperçu nutritionnel
        self.nutritionChanged.emit(calories, proteines, glucides, lipides, fibres)

        # Créer le texte HTML avec un style plus moderne
        html = f"""
        <h3 style="margin-top:0;">{aliment['nom']}</h3>
        <p>
            <span style="color:#666;">Marque:</span> <b>{aliment.get('marque', 'Non spécifiée')}</b><br>
            <span style="color:#666;">Catégorie:</span> <b>{aliment.get('categorie', 'Non spécifiée')}</b>
        </p>
        <div style="background-color: #f0f4f8; border-radius: 5px; padding: 8px; border: 1px solid #e9ecef;">
            <h4 style="margin-top:0; margin-bottom:5px; color:#2c3e50;">Valeurs nutritionnelles pour {quantite}g:</h4>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Calories:</span></td>
                    <td align="right"><b>{calories:.0f} kcal</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Protéines:</span></td>
                    <td align="right"><b>{proteines:.1f}g</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Glucides:</span></td>
                    <td align="right"><b>{glucides:.1f}g</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Lipides:</span></td>
                    <td align="right"><b>{lipides:.1f}g</b></td>
                </tr>
        """

        # Ajouter les fibres si disponibles
        if aliment.get("fibres"):
            fibres = aliment["fibres"] * quantite / 100
            html += f"""<tr>
                    <td style="padding:3px;"><span style="color:#666;">Fibres:</span></td>
                    <td align="right"><b>{fibres:.1f}g</b></td>
                </tr>"""

        # Ajouter le prix si disponible
        if aliment.get("prix_kg"):
            prix = (aliment["prix_kg"] / 1000) * quantite
            html += f"""<tr>
                    <td style="padding:3px;"><span style="color:#666;">Coût:</span></td>
                    <td align="right"><b>{prix:.2f}€</b></td>
                </tr>"""

        html += """
            </table>
        </div>
        """

        self.details_label.setText(html)

    def update_compose_details(self):
        """Met à jour les détails de l'aliment composé sélectionné"""
        if self.selected_aliment_compose_id is None:
            self.details_label.setText("")
            self.nutritionChanged.emit(0, 0, 0, 0, 0)  # Réinitialiser l'aperçu
            return

        aliment = self.db_manager.get_aliment_compose(self.selected_aliment_compose_id)
        if not aliment:
            return

        # Récupérer la quantité sélectionnée
        quantite = self.quantite_spin.value()

        # Calculer le facteur d'échelle
        facteur = quantite / 100.0

        # Calculer les valeurs
        calories = aliment["total_calories"] * facteur
        proteines = aliment["total_proteines"] * facteur
        glucides = aliment["total_glucides"] * facteur
        lipides = aliment["total_lipides"] * facteur
        fibres = aliment.get("total_fibres", 0) * facteur

        # Émettre le signal pour mettre à jour l'aperçu nutritionnel
        self.nutritionChanged.emit(calories, proteines, glucides, lipides, fibres)

        # Créer le texte HTML avec un style plus moderne
        html = f"""
        <h3 style="margin-top:0;">{aliment['nom']}</h3>
        <p style="color:#666;">{aliment.get('description', '')}</p>
        
        <div style="background-color: #f0f4f8; border-radius: 5px; padding: 8px; border: 1px solid #e9ecef; margin-bottom: 10px;">
            <h4 style="margin-top:0; margin-bottom:5px; color:#2c3e50;">Composition pour {quantite}g:</h4>
            <ul style="margin-top:5px; color:#555; padding-left: 20px;">
        """

        # Liste des ingrédients
        for ingredient in aliment["ingredients"]:
            ing_quantite = ingredient["quantite"] * facteur
            html += f"<li><b>{ingredient['nom']}:</b> {ing_quantite:.0f}g</li>"

        html += f"""
            </ul>
        </div>
        
        <div style="background-color: #f0f4f8; border-radius: 5px; padding: 8px; border: 1px solid #e9ecef;">
            <h4 style="margin-top:0; margin-bottom:5px; color:#2c3e50;">Valeurs nutritionnelles pour {quantite}g:</h4>
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Calories:</span></td>
                    <td align="right"><b>{calories:.0f} kcal</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Protéines:</span></td>
                    <td align="right"><b>{proteines:.1f}g</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Glucides:</span></td>
                    <td align="right"><b>{glucides:.1f}g</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Lipides:</span></td>
                    <td align="right"><b>{lipides:.1f}g</b></td>
                </tr>
                <tr>
                    <td style="padding:3px;"><span style="color:#666;">Fibres:</span></td>
                    <td align="right"><b>{fibres:.1f}g</b></td>
                </tr>
            </table>
        </div>
        """

        self.details_label.setText(html)

    def open_compose_manager(self):
        """Ouvre le gestionnaire d'aliments composés"""
        from src.ui.dialogs.aliment_compose_dialog import AlimentsComposesManagerDialog

        dialog = AlimentsComposesManagerDialog(self, self.db_manager)
        if dialog.exec():
            # Recharger les aliments composés après gestion
            self.load_aliments_composes()

    def get_data(self):
        """Retourne l'ID de l'aliment ou de l'aliment composé et la quantité sélectionnés"""
        if self.mode_aliment_compose:
            # Mode aliment composé: retourner un tuple spécial
            return (
                "compose",
                self.selected_aliment_compose_id,
                self.quantite_spin.value(),
            )
        else:
            # Mode aliment simple: retourner l'ancien format
            return (self.selected_aliment_id, self.quantite_spin.value())

    def init_nutrition_preview(self):
        """Initialise l'affichage des valeurs nutritionnelles"""
        # Valeurs actuelles
        cal_actuel = self.valeurs_actuelles.get("calories", 0)
        prot_actuel = self.valeurs_actuelles.get("proteines", 0)
        gluc_actuel = self.valeurs_actuelles.get("glucides", 0)
        lip_actuel = self.valeurs_actuelles.get("lipides", 0)

        # Objectifs
        cal_obj = self.objectifs.get("calories", 2500)
        prot_obj = self.objectifs.get("proteines", 150)
        gluc_obj = self.objectifs.get("glucides", 250)
        lip_obj = self.objectifs.get("lipides", 80)

        # Calculer les pourcentages
        cal_pct = cal_actuel / cal_obj if cal_obj > 0 else 0
        prot_pct = prot_actuel / prot_obj if prot_obj > 0 else 0
        gluc_pct = gluc_actuel / gluc_obj if gluc_obj > 0 else 0
        lip_pct = lip_actuel / lip_obj if lip_obj > 0 else 0

        # Configurer les barres de progression actuelles
        self.cal_progress.setMaximum(cal_obj * 1.2)  # Maximum à 120% de l'objectif
        self.cal_progress.setValue(min(cal_actuel, cal_obj * 1.2))
        self.cal_progress.setFormat(f"{cal_pct*100:.0f}%")
        self.cal_value.setText(f"{cal_actuel:.0f} / {cal_obj:.0f} kcal")

        self.prot_progress.setMaximum(prot_obj * 1.2)
        self.prot_progress.setValue(min(prot_actuel, prot_obj * 1.2))
        self.prot_progress.setFormat(f"{prot_pct*100:.0f}%")
        self.prot_value.setText(f"{prot_actuel:.1f} / {prot_obj:.0f} g")

        self.gluc_progress.setMaximum(gluc_obj * 1.2)
        self.gluc_progress.setValue(min(gluc_actuel, gluc_obj * 1.2))
        self.gluc_progress.setFormat(f"{gluc_pct*100:.0f}%")
        self.gluc_value.setText(f"{gluc_actuel:.1f} / {gluc_obj:.0f} g")

        self.lip_progress.setMaximum(lip_obj * 1.2)
        self.lip_progress.setValue(min(lip_actuel, lip_obj * 1.2))
        self.lip_progress.setFormat(f"{lip_pct*100:.0f}%")
        self.lip_value.setText(f"{lip_actuel:.1f} / {lip_obj:.0f} g")

        # Initialiser les barres "après ajout" avec les mêmes valeurs
        self.cal_after_progress.setMaximum(cal_obj * 1.2)
        self.cal_after_progress.setValue(min(cal_actuel, cal_obj * 1.2))
        self.cal_after_progress.setFormat(f"{cal_pct*100:.0f}%")
        self.cal_after_value.setText(f"{cal_actuel:.0f} / {cal_obj:.0f} kcal")

        self.prot_after_progress.setMaximum(prot_obj * 1.2)
        self.prot_after_progress.setValue(min(prot_actuel, prot_obj * 1.2))
        self.prot_after_progress.setFormat(f"{prot_pct*100:.0f}%")
        self.prot_after_value.setText(f"{prot_actuel:.1f} / {prot_obj:.0f} g")

        self.gluc_after_progress.setMaximum(gluc_obj * 1.2)
        self.gluc_after_progress.setValue(min(gluc_actuel, gluc_obj * 1.2))
        self.gluc_after_progress.setFormat(f"{gluc_pct*100:.0f}%")
        self.gluc_after_value.setText(f"{gluc_actuel:.1f} / {gluc_obj:.0f} g")

        self.lip_after_progress.setMaximum(lip_obj * 1.2)
        self.lip_after_progress.setValue(min(lip_actuel, lip_obj * 1.2))
        self.lip_after_progress.setFormat(f"{lip_pct*100:.0f}%")
        self.lip_after_value.setText(f"{lip_actuel:.1f} / {lip_obj:.0f} g")

        # Définir les statuts des barres en fonction des pourcentages
        self.set_progress_bar_status(self.cal_progress, cal_pct)
        self.set_progress_bar_status(self.prot_progress, prot_pct)
        self.set_progress_bar_status(self.gluc_progress, gluc_pct)
        self.set_progress_bar_status(self.lip_progress, lip_pct)

        # Dupliquer pour les barres "après"
        self.set_progress_bar_status(self.cal_after_progress, cal_pct)
        self.set_progress_bar_status(self.prot_after_progress, prot_pct)
        self.set_progress_bar_status(self.gluc_after_progress, gluc_pct)
        self.set_progress_bar_status(self.lip_after_progress, lip_pct)

    def update_nutrition_preview(
        self, calories, proteines, glucides, lipides, fibres=0
    ):
        """Met à jour l'affichage des valeurs nutritionnelles après ajout"""
        # Valeurs actuelles
        cal_actuel = self.valeurs_actuelles.get("calories", 0)
        prot_actuel = self.valeurs_actuelles.get("proteines", 0)
        gluc_actuel = self.valeurs_actuelles.get("glucides", 0)
        lip_actuel = self.valeurs_actuelles.get("lipides", 0)

        # Objectifs
        cal_obj = self.objectifs.get("calories", 2500)
        prot_obj = self.objectifs.get("proteines", 150)
        gluc_obj = self.objectifs.get("glucides", 250)
        lip_obj = self.objectifs.get("lipides", 80)

        # Calculer les nouvelles valeurs
        cal_new = cal_actuel + calories
        prot_new = prot_actuel + proteines
        gluc_new = gluc_actuel + glucides
        lip_new = lip_actuel + lipides

        # Calculer les pourcentages
        cal_pct = cal_new / cal_obj if cal_obj > 0 else 0
        prot_pct = prot_new / prot_obj if prot_obj > 0 else 0
        gluc_pct = gluc_new / gluc_obj if gluc_obj > 0 else 0
        lip_pct = lip_new / lip_obj if lip_obj > 0 else 0

        # Mettre à jour les barres "après ajout"
        self.cal_after_progress.setValue(min(cal_new, cal_obj * 1.2))
        self.cal_after_progress.setFormat(f"{cal_pct*100:.0f}%")
        self.cal_after_value.setText(f"{cal_new:.0f} / {cal_obj:.0f} kcal")

        self.prot_after_progress.setValue(min(prot_new, prot_obj * 1.2))
        self.prot_after_progress.setFormat(f"{prot_pct*100:.0f}%")
        self.prot_after_value.setText(f"{prot_new:.1f} / {prot_obj:.0f} g")

        self.gluc_after_progress.setValue(min(gluc_new, gluc_obj * 1.2))
        self.gluc_after_progress.setFormat(f"{gluc_pct*100:.0f}%")
        self.gluc_after_value.setText(f"{gluc_new:.1f} / {gluc_obj:.0f} g")

        self.lip_after_progress.setValue(min(lip_new, lip_obj * 1.2))
        self.lip_after_progress.setFormat(f"{lip_pct*100:.0f}%")
        self.lip_after_value.setText(f"{lip_new:.1f} / {lip_obj:.0f} g")

        # Mettre à jour les statuts/couleurs des barres "après ajout"
        self.set_progress_bar_status(self.cal_after_progress, cal_pct)
        self.set_progress_bar_status(self.prot_after_progress, prot_pct)
        self.set_progress_bar_status(self.gluc_after_progress, gluc_pct)
        self.set_progress_bar_status(self.lip_after_progress, lip_pct)

    def set_progress_bar_status(self, progress_bar, percentage):
        """Définit le statut (et donc la couleur) de la barre de progression selon le pourcentage"""
        # Vérifier si target est zéro pour éviter la division par zéro
        if percentage == float("inf") or percentage != percentage:  # inf ou NaN
            percentage = 0  # Valeur par défaut sécuritaire

        # Déterminer le statut basé sur le pourcentage
        if percentage > self.THRESHOLD_OVER:  # >105%
            status = "over"  # Rouge - trop élevé
        elif self.THRESHOLD_GOOD_LOWER <= percentage <= self.THRESHOLD_GOOD_UPPER:
            status = "good"  # Vert - idéal
        elif self.THRESHOLD_LOW <= percentage < self.THRESHOLD_GOOD_LOWER:
            status = "medium"  # Orange - moyen
        else:  # <50%
            status = "low"  # Gris - trop bas

        # Appliquer le statut comme propriété QSS
        progress_bar.setProperty("status", status)

        # Forcer le rafraîchissement du style
        progress_bar.style().unpolish(progress_bar)
        progress_bar.style().polish(progress_bar)
