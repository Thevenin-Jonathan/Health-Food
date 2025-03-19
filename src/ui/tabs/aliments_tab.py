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
from PySide6.QtGui import QIcon

from src.ui.dialogs.aliment_dialog import AlimentDialog
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


class ActionButton(QPushButton):
    """Bouton d'action personnalisé pour les cellules du tableau"""

    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(80)
        self.setMaximumWidth(80)
        self.setMinimumHeight(20)
        self.setMaximumHeight(22)
        if icon:
            self.setIcon(QIcon(icon))

        # Réduire la taille de police de 2px
        font = self.font()
        font.setPixelSize(
            max(font.pixelSize() - 2, 8)
        )  # Éviter les tailles trop petites
        self.setFont(font)


class ButtonContainer(QWidget):
    """Widget conteneur pour centrer un bouton dans une cellule de tableau"""

    def __init__(self, button, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Marges réduites
        layout.setAlignment(Qt.AlignCenter)  # Alignement centré
        layout.addWidget(button)
        self.setLayout(layout)


class AlimentsTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Ajouter une zone de filtrage
        filter_layout = QHBoxLayout()

        # Recherche par texte
        self.search_label = QLabel("Recherche:")
        filter_layout.addWidget(self.search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez un nom ou mot-clé...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)

        # Filtre par catégorie
        self.category_label = QLabel("Catégorie:")
        filter_layout.addWidget(self.category_label)

        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(120)
        self.category_combo.addItem("Toutes", "")
        categories = self.db_manager.get_categories_uniques()
        for cat in categories:
            self.category_combo.addItem(cat, cat)
        self.category_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_combo)

        # Filtre par marque
        self.marque_label = QLabel("Marque:")
        filter_layout.addWidget(self.marque_label)

        self.marque_combo = QComboBox()
        self.marque_combo.setMinimumWidth(120)
        self.marque_combo.addItem("Toutes", "")
        marques = self.db_manager.get_marques_uniques()
        for marque in marques:
            if marque:  # Éviter les valeurs vides
                self.marque_combo.addItem(marque, marque)
        self.marque_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.marque_combo)

        # Filtre par magasin
        self.magasin_label = QLabel("Magasin:")
        filter_layout.addWidget(self.magasin_label)

        self.magasin_combo = QComboBox()
        self.magasin_combo.setMinimumWidth(120)
        self.magasin_combo.addItem("Tous", "")
        magasins = self.db_manager.get_magasins_uniques()
        for magasin in magasins:
            if magasin:  # Éviter les valeurs vides
                self.magasin_combo.addItem(magasin, magasin)
        self.magasin_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.magasin_combo)

        # Bouton pour réinitialiser les filtres
        self.reset_filter_btn = QPushButton("Réinitialiser")
        self.reset_filter_btn.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_filter_btn)

        filter_layout.addStretch()

        self.btn_add = QPushButton("Ajouter un aliment")
        self.btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self.btn_add.clicked.connect(self.add_aliment)
        filter_layout.addWidget(self.btn_add)

        main_layout.addLayout(filter_layout)

        # Tableau des aliments avec les colonnes de boutons d'action
        self.table = QTableWidget()
        self.table.setColumnCount(13)  # 11 colonnes de données + 2 colonnes d'actions
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nom",
                "Marque",
                "Magasin",
                "Catégorie",
                "Calories",
                "Protéines",
                "Glucides",
                "Lipides",
                "Fibres",
                "Prix/kg",
                "Modifier",  # Nouvelle colonne pour le bouton Modifier
                "Supprimer",  # Nouvelle colonne pour le bouton Supprimer
            ]
        )

        # Configuration du tableau
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Lecture seule
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Masquer la colonne ID
        self.table.hideColumn(0)

        # Définir une taille minimale pour le tableau
        self.table.setMinimumWidth(1000)
        self.table.setMinimumHeight(500)
        main_layout.addWidget(self.table)

        # Configuration des largeurs de colonnes
        header = self.table.horizontalHeader()

        # Définir les largeurs des colonnes
        col_widths = {
            1: 140,  # Nom
            2: 100,  # Marque
            3: 100,  # Magasin
            4: 100,  # Catégorie
            5: 70,  # Calories
            6: 70,  # Protéines
            7: 70,  # Glucides
            8: 70,  # Lipides
            9: 70,  # Fibres
            10: 70,  # Prix/kg
            11: 70,  # Bouton Modifier
            12: 70,  # Bouton Supprimer
        }

        # Appliquer les largeurs définies
        for col, width in col_widths.items():
            self.table.setColumnWidth(col, width)
            if col in [11, 12]:  # Colonnes des boutons
                header.setSectionResizeMode(col, QHeaderView.Fixed)
            else:
                header.setSectionResizeMode(col, QHeaderView.Interactive)

        # La colonne Nom est extensible mais avec une largeur minimale
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setMinimumSectionSize(100)

        # Ajouter des tooltips
        self.table.horizontalHeaderItem(5).setToolTip("Calories pour 100g")
        self.table.horizontalHeaderItem(6).setToolTip("Protéines en g pour 100g")
        self.table.horizontalHeaderItem(7).setToolTip("Glucides en g pour 100g")
        self.table.horizontalHeaderItem(8).setToolTip("Lipides en g pour 100g")
        self.table.horizontalHeaderItem(9).setToolTip("Fibres en g pour 100g")

    def refresh_data(self):
        """Implémentation de la méthode de base - rafraîchit les données"""
        self.load_data()

    def load_data(self, sort_column="nom", sort_order=True):
        """Charge les aliments dans le tableau avec option de tri"""
        self.load_data_filtered(
            None,  # category
            None,  # marque
            None,  # magasin
            None,  # search_text
            sort_column,
            sort_order,
        )

    def load_data_filtered(
        self,
        category=None,
        marque=None,
        magasin=None,
        search_text=None,
        sort_column="nom",
        sort_order=True,
    ):
        """Charge les aliments filtrés dans le tableau"""
        # Désactiver temporairement le tri pendant le chargement
        self.table.setSortingEnabled(False)

        # Mémoriser la colonne et l'ordre de tri actuels
        current_sort_column = self.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.table.horizontalHeader().sortIndicatorOrder()

        # Déterminer la colonne et l'ordre de tri
        if self.table.isSortingEnabled() and current_sort_column > 0:
            sort_column = {
                1: "nom",
                2: "marque",
                3: "magasin",
                4: "categorie",
                5: "calories",
                6: "proteines",
                7: "glucides",
                8: "lipides",
                9: "fibres",
                10: "prix_kg",
            }.get(current_sort_column, "nom")
            sort_order = current_sort_order == Qt.AscendingOrder

        # Vider le tableau
        self.table.setRowCount(0)

        # Charger les aliments avec les filtres
        aliments = self.db_manager.get_aliments(
            categorie=category,
            marque=marque,
            magasin=magasin,
            recherche=search_text if search_text else None,
            sort_column=sort_column,
            sort_order=sort_order,
        )

        # Remplir le tableau
        self.table.setRowCount(len(aliments))
        for i, aliment in enumerate(aliments):
            # ID (caché)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, aliment["id"])
            self.table.setItem(i, 0, id_item)

            # Nom
            self.table.setItem(i, 1, QTableWidgetItem(aliment["nom"]))

            # Marque
            self.table.setItem(i, 2, QTableWidgetItem(aliment["marque"] or ""))

            # Magasin
            self.table.setItem(i, 3, QTableWidgetItem(aliment["magasin"] or ""))

            # Catégorie
            self.table.setItem(i, 4, QTableWidgetItem(aliment["categorie"] or ""))

            # Valeurs nutritionnelles avec tri numérique correct
            cal_item = NumericTableItem(
                aliment["calories"], f"{aliment['calories']:.0f}"
            )
            self.table.setItem(i, 5, cal_item)

            prot_item = NumericTableItem(
                aliment["proteines"], f"{aliment['proteines']:.1f}"
            )
            self.table.setItem(i, 6, prot_item)

            gluc_item = NumericTableItem(
                aliment["glucides"], f"{aliment['glucides']:.1f}"
            )
            self.table.setItem(i, 7, gluc_item)

            lip_item = NumericTableItem(aliment["lipides"], f"{aliment['lipides']:.1f}")
            self.table.setItem(i, 8, lip_item)

            # Fibres
            fibres_val = aliment.get("fibres", 0) or 0
            fibres_item = NumericTableItem(fibres_val, f"{fibres_val:.1f}")
            self.table.setItem(i, 9, fibres_item)

            # Prix au kg avec tri numérique correct
            prix_val = aliment.get("prix_kg", 0) or 0
            prix_item = NumericTableItem(prix_val)
            if prix_val > 0:
                prix_item.setText(f"{prix_val:.2f} €")
            self.table.setItem(i, 10, prix_item)

            # Ajouter les boutons comme avant...
            # Bouton Modifier
            btn_edit = ActionButton("Modifier")
            btn_edit.setStyleSheet(
                """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                """
            )
            btn_edit.clicked.connect(
                lambda checked, row=i: self.edit_aliment_from_button(row)
            )
            # Utiliser le conteneur pour centrer le bouton
            edit_container = ButtonContainer(btn_edit)
            self.table.setCellWidget(i, 11, edit_container)

            # Bouton Supprimer
            btn_delete = ActionButton("Supprimer")
            btn_delete.setStyleSheet(
                """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                """
            )
            btn_delete.clicked.connect(
                lambda checked, row=i: self.delete_aliment_from_button(row)
            )
            # Utiliser le conteneur pour centrer le bouton
            delete_container = ButtonContainer(btn_delete)
            self.table.setCellWidget(i, 12, delete_container)

        # Réactiver le tri avec la même colonne et ordre qu'avant
        self.table.setSortingEnabled(True)
        if current_sort_column > 0:
            self.table.sortItems(current_sort_column, current_sort_order)

    def apply_filters(self):
        """Applique les filtres sélectionnés"""
        search_text = self.search_input.text().strip()
        category = self.category_combo.currentData()
        marque = self.marque_combo.currentData()
        magasin = self.magasin_combo.currentData()

        # Charger les données filtrées
        self.load_data_filtered(category, marque, magasin, search_text)

    def reset_filters(self):
        """Réinitialise les filtres"""
        self.search_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.marque_combo.setCurrentIndex(0)
        self.magasin_combo.setCurrentIndex(0)
        self.load_data()

    def edit_aliment_from_button(self, row):
        """Éditer un aliment depuis le bouton dans le tableau"""
        aliment_id = int(self.table.item(row, 0).text())
        self.edit_aliment_by_id(aliment_id)

    def delete_aliment_from_button(self, row):
        """Supprimer un aliment depuis le bouton dans le tableau"""
        aliment_id = int(self.table.item(row, 0).text())
        self.delete_aliment_by_id(aliment_id)

    def edit_aliment_by_id(self, aliment_id):
        """Édite un aliment par son ID"""
        # Récupérer les données de l'aliment
        aliment = self.db_manager.get_aliment(aliment_id)

        # Récupérer les listes de données existantes
        magasins = self.db_manager.get_magasins_uniques()
        marques = self.db_manager.get_marques_uniques()
        categories = self.db_manager.get_categories_uniques()

        dialog = AlimentDialog(
            self,
            aliment=aliment,
            magasins=magasins,
            marques=marques,
            categories=categories,
        )

        if dialog.exec():
            data = dialog.get_data()
            self.db_manager.modifier_aliment(aliment_id, data)

            # Émettre le signal pour notifier les autres composants
            EVENT_BUS.aliment_modifie.emit(aliment_id)
            EVENT_BUS.aliments_modifies.emit()

            self.load_data()

    def delete_aliment_by_id(self, aliment_id):
        """Supprime un aliment par son ID avec confirmation"""
        # Trouver le nom de l'aliment pour la confirmation
        for row in range(self.table.rowCount()):
            if int(self.table.item(row, 0).text()) == aliment_id:
                aliment_nom = self.table.item(row, 1).text()
                break
        else:
            aliment_nom = f"Aliment #{aliment_id}"

        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer l'aliment '{aliment_nom}' ?\n\n"
            "Attention: cette action supprimera également cet aliment de tous les repas où il est utilisé.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_aliment(aliment_id)

            # Émettre le signal pour notifier les autres composants
            EVENT_BUS.aliment_supprime.emit(aliment_id)
            EVENT_BUS.aliments_modifies.emit()

            self.load_data()

    def add_aliment(self):
        """Ajoute un nouvel aliment"""
        # Récupérer les listes de données existantes
        magasins = self.db_manager.get_magasins_uniques()
        marques = self.db_manager.get_marques_uniques()
        categories = self.db_manager.get_categories_uniques()

        dialog = AlimentDialog(
            self, magasins=magasins, marques=marques, categories=categories
        )

        if dialog.exec():
            data = dialog.get_data()
            aliment_id = self.db_manager.ajouter_aliment(data)

            # Émettre le signal pour notifier les autres composants
            EVENT_BUS.aliment_ajoute.emit(aliment_id)
            EVENT_BUS.aliments_modifies.emit()

            self.load_data()

    def edit_aliment(self):
        """Méthode conservée pour compatibilité avec le menu contextuel"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner un aliment à modifier.",
            )
            return

        # Récupérer l'ID de la ligne sélectionnée
        row = selected_rows[0].row()
        aliment_id = int(self.table.item(row, 0).text())
        self.edit_aliment_by_id(aliment_id)

    def delete_aliment(self):
        """Méthode conservée pour compatibilité avec le menu contextuel"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner un aliment à supprimer.",
            )
            return

        # Récupérer l'ID de la ligne sélectionnée
        row = selected_rows[0].row()
        aliment_id = int(self.table.item(row, 0).text())
        self.delete_aliment_by_id(aliment_id)

    def show_context_menu(self, position):
        """Affiche un menu contextuel pour les actions rapides"""
        menu = QMenu()

        edit_action = menu.addAction("Modifier")
        delete_action = menu.addAction("Supprimer")

        action = menu.exec_(self.table.mapToGlobal(position))

        # Exécuter l'action choisie
        if action == edit_action:
            self.edit_aliment()
        elif action == delete_action:
            self.delete_aliment()
