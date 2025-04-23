from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
)
from PySide6.QtCore import Qt

from src.ui.dialogs.aliment_compose_dialog import AlimentComposeDialog
from src.utils.events import EVENT_BUS
from .tab_base import TabBase


# Classe personnalisée pour les éléments de tableau avec tri numérique correct
class NumericTableItem(QTableWidgetItem):
    def __init__(self, value, text="", unit=""):
        super().__init__()
        self.set_value(value)
        if text:
            self.setText(text)
        else:
            self.format_value(value, unit)

    def set_value(self, value):
        self.setData(Qt.UserRole, float(value) if value is not None else 0.0)

    def format_value(self, value, unit):
        if value and value > 0:
            if unit:
                self.setText(f"{value:.2f} {unit}")
            else:
                self.setText(f"{value:.2f}")
        else:
            self.setText("")

    def __lt__(self, other):
        my_value = self.data(Qt.UserRole)
        other_value = other.data(Qt.UserRole)

        # Placer les valeurs nulles/0 à la fin lors du tri ascendant
        if my_value == 0 and other_value > 0:
            return False
        if other_value == 0 and my_value > 0:
            return True

        return my_value < other_value


class ButtonContainer(QWidget):
    """Widget conteneur pour centrer un bouton dans une cellule de tableau"""

    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.setProperty("class", "button-container")  # Pour le ciblage CSS
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Marges réduites
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)  # Alignement centré
        layout.addWidget(button)
        self.setLayout(layout)


class AlimentsComposesTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)

        # Attributs pour les filtres
        self.search_input = QLineEdit()
        self.category_combo = None
        self.reset_filter_btn = None
        self.btn_add = None

        # Tableau principal
        self.table = None

        # Configuration de l'interface
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Créer un layout principal sans marges pour le widget entier
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Créer un layout horizontal pour centrer le contenu
        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Créer un widget contenant le contenu réel avec sa largeur limitée
        content_widget = QWidget()
        content_widget.setMaximumWidth(1200)  # Largeur maximale
        content_widget.setMinimumWidth(900)  # Largeur minimale

        # Layout pour le contenu principal
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Titre de la page
        title = QLabel("<h1>Mes Aliments Composés</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Sous-titre explicatif
        subtitle = QLabel("Gérez vos mélanges et combinaisons d'aliments personnalisés")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        # Configuration des filtres et du tableau
        self._setup_filters(main_layout)
        self._setup_table(main_layout)

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

    def _setup_filters(self, main_layout):
        """Configure les filtres et recherche"""
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Recherche par texte
        search_label = QLabel("Recherche:")
        filter_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez un nom ou mot-clé...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.apply_filters)
        self.search_input.setMinimumWidth(180)
        filter_layout.addWidget(self.search_input)

        # Filtre par catégorie
        category_label = QLabel("Catégorie:")
        filter_layout.addWidget(category_label)

        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(150)
        self.category_combo.addItem("Toutes les catégories", "")
        categories = self.db_manager.get_categories_aliments_composes()
        for categorie in categories:
            self.category_combo.addItem(categorie, categorie)
        self.category_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_combo)

        # Bouton pour réinitialiser les filtres
        self.reset_filter_btn = QPushButton("Réinitialiser")
        self.reset_filter_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_filter_btn)

        filter_layout.addStretch()

        # Bouton d'ajout
        self.btn_add = QPushButton("Créer un aliment composé")
        self.btn_add.setObjectName("primaryButton")
        self.btn_add.clicked.connect(self.add_aliment_compose)
        filter_layout.addWidget(self.btn_add)

        main_layout.addLayout(filter_layout)

    def _setup_table(self, main_layout):
        """Configure le tableau des aliments composés"""
        # Tableau des aliments composés
        self.table = QTableWidget()
        self.table.setObjectName("alimentsComposesTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Suppr.", "Nom", "Catégorie", "Calories", "Nb ingrédients"]
        )

        # Configuration du tableau
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Lecture seule
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Connecter le double clic sur une ligne à l'édition
        self.table.cellDoubleClicked.connect(self.edit_aliment_from_double_click)

        # Masquer la colonne ID
        self.table.hideColumn(0)

        # Configuration des largeurs de colonnes
        header = self.table.horizontalHeader()

        # Désactiver le défilement horizontal
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Définir les largeurs des colonnes
        col_widths = {
            1: (60, QHeaderView.Fixed),  # Colonne Supprimer
            2: (250, QHeaderView.Stretch),  # Nom - largeur dynamique
            3: (150, QHeaderView.Fixed),  # Catégorie
            4: (80, QHeaderView.Fixed),  # Calories
            5: (100, QHeaderView.Fixed),  # Nb ingrédients
        }

        # Appliquer les largeurs fixes pour les colonnes qui ne sont pas en Stretch
        for col, (width, mode) in col_widths.items():
            if mode == QHeaderView.Fixed:
                self.table.setColumnWidth(col, width)
            header.setSectionResizeMode(col, mode)

        # Désactiver l'étirement de la dernière section
        header.setStretchLastSection(False)

        # Centrer le contenu des colonnes numériques
        for col in range(4, 6):
            self.table.horizontalHeaderItem(col).setTextAlignment(Qt.AlignCenter)

        # Définir une hauteur de ligne raisonnable
        self.table.verticalHeader().setDefaultSectionSize(40)  # Hauteur de ligne
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # Masquer les en-têtes de ligne
        self.table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table)

    def refresh_data(self):
        """Implémentation de la méthode de base - rafraîchit les données"""
        self.load_data()

    def load_data(self):
        """Charge les aliments composés dans le tableau"""
        self.load_data_filtered(None, None)

    def load_data_filtered(self, categorie=None, recherche=None):
        """Charge les aliments composés filtrés dans le tableau"""
        # Désactiver temporairement le tri pendant le chargement
        self.table.setSortingEnabled(False)

        # Mémoriser la colonne et l'ordre de tri actuels
        current_sort_column = self.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.table.horizontalHeader().sortIndicatorOrder()

        # Vider le tableau
        self.table.setRowCount(0)

        # Charger les aliments composés
        aliments = self.db_manager.get_aliments_composes(categorie)

        # Filtrer par recherche si nécessaire
        if recherche:
            recherche = recherche.lower()
            aliments = [
                a
                for a in aliments
                if recherche in a["nom"].lower()
                or (a.get("description") and recherche in a["description"].lower())
            ]

        # Remplir le tableau
        self.table.setRowCount(len(aliments))
        for i, aliment in enumerate(aliments):
            # ID (caché)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, aliment["id"])
            self.table.setItem(i, 0, id_item)

            # Bouton Supprimer
            btn_delete = QPushButton("〤")
            btn_delete.setObjectName("deleteButton")
            aliment_id = aliment["id"]
            btn_delete.clicked.connect(
                lambda checked, aid=aliment_id: self.delete_aliment_by_id(aid)
            )
            delete_container = ButtonContainer(btn_delete)
            self.table.setCellWidget(i, 1, delete_container)

            # Nom
            nom_item = QTableWidgetItem(aliment["nom"])
            nom_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(i, 2, nom_item)

            # Catégorie
            categorie_item = QTableWidgetItem(aliment.get("categorie", ""))
            categorie_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(i, 3, categorie_item)

            # Calories
            calories = aliment.get("total_calories", 0)
            cal_item = NumericTableItem(calories, f"{calories:.0f} kcal")
            cal_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 4, cal_item)

            # Nombre d'ingrédients
            nb_ingredients = len(aliment.get("ingredients", []))
            nb_ing_item = NumericTableItem(nb_ingredients, str(nb_ingredients))
            nb_ing_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 5, nb_ing_item)

        # Réactiver le tri avec la même colonne et ordre qu'avant
        self.table.setSortingEnabled(True)
        if current_sort_column > 0:
            self.table.sortItems(current_sort_column, current_sort_order)

    def apply_filters(self):
        """Applique les filtres sélectionnés"""
        search_text = self.search_input.text().strip()
        category = self.category_combo.currentData()
        self.load_data_filtered(category, search_text)

    def reset_filters(self):
        """Réinitialise les filtres"""
        self.search_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.load_data()

    def add_aliment_compose(self):
        """Ajoute un nouvel aliment composé"""
        dialog = AlimentComposeDialog(self, self.db_manager)
        dialog.aliment_ajoute.connect(lambda _: self.refresh_data())
        dialog.exec()

    def edit_aliment_by_id(self, aliment_id):
        """Édite un aliment composé par son ID"""
        aliment = self.db_manager.get_aliment_compose(aliment_id)
        if not aliment:
            QMessageBox.warning(
                self,
                "Erreur",
                "Impossible de récupérer les données de l'aliment composé.",
            )
            return

        dialog = AlimentComposeDialog(self, self.db_manager, aliment)
        dialog.aliment_modifie.connect(lambda _: self.refresh_data())
        dialog.exec()

    def delete_aliment_by_id(self, aliment_id):
        """Supprime un aliment composé par son ID"""
        aliment = self.db_manager.get_aliment_compose(aliment_id)
        if not aliment:
            return

        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer l'aliment composé '{aliment['nom']}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            result = self.db_manager.supprimer_aliment_compose(aliment_id)
            if result:
                # Émettre le signal pour notifier les autres composants
                EVENT_BUS.aliments_modifies.emit()  # Signal générique
                self.load_data()
            else:
                QMessageBox.warning(
                    self,
                    "Erreur de suppression",
                    f"Impossible de supprimer l'aliment composé '{aliment['nom']}'.",
                )

    def show_context_menu(self, position):
        """Affiche un menu contextuel pour les actions rapides"""
        # Trouver l'index de la ligne sous le curseur
        index = self.table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        aliment_id = int(self.table.item(row, 0).text())

        menu = QMenu()
        edit_action = menu.addAction("Modifier")
        delete_action = menu.addAction("Supprimer")

        action = menu.exec_(self.table.mapToGlobal(position))

        # Exécuter l'action choisie
        if action == edit_action:
            self.edit_aliment_by_id(aliment_id)
        elif action == delete_action:
            self.delete_aliment_by_id(aliment_id)

    def edit_aliment_from_double_click(self, row, column):
        """Éditer un aliment composé depuis un double-clic sur une ligne du tableau"""
        # Ignorer les clics sur la colonne de suppression
        if column == 1:
            return

        aliment_id = int(self.table.item(row, 0).text())
        self.edit_aliment_by_id(aliment_id)
