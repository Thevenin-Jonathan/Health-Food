from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QAction

from .tab_base import TabBase
from ..dialogs.aliment_dialog import AlimentDialog
from ...database.models import Aliment
from ...utils.config import BUTTON_STYLES


# Classe personnalisée pour les éléments de tableau avec tri numérique correct
class NumericTableItem(QTableWidgetItem):
    def __init__(self, value, text="", unit=""):
        super().__init__()
        self.setValue(value)
        if text:
            self.setText(text)
        else:
            self.formatValue(value, unit)

    def setValue(self, value):
        self.setData(Qt.UserRole, float(value) if value is not None else 0.0)

    def formatValue(self, value, unit):
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


class AlimentsTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Tableau des aliments avec toutes les colonnes nécessaires
        self.table = QTableWidget()
        self.table.setColumnCount(11)  # Augmenter le nombre de colonnes
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
            ]
        )

        # Configuration du tableau
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Lecture seule
        self.table.setSortingEnabled(
            True
        )  # Permettre le tri en cliquant sur les en-têtes
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Masquer la colonne ID
        self.table.hideColumn(0)

        # Définir une taille minimale pour le tableau
        self.table.setMinimumWidth(900)
        self.table.setMinimumHeight(500)
        main_layout.addWidget(self.table)

        # Boutons d'action
        buttons_layout = QHBoxLayout()

        self.btn_add = QPushButton("Ajouter un aliment")
        self.btn_add.clicked.connect(self.add_aliment)

        self.btn_edit = QPushButton("Modifier l'aliment sélectionné")
        self.btn_edit.clicked.connect(self.edit_aliment)

        self.btn_delete = QPushButton("Supprimer l'aliment sélectionné")
        self.btn_delete.clicked.connect(self.delete_aliment)

        self.btn_refresh = QPushButton("Actualiser la liste")
        self.btn_refresh.clicked.connect(self.refresh_data)

        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_edit)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def refresh_data(self):
        """Implémentation de la méthode de base - rafraîchit les données"""
        self.load_data()

    def load_data(self, sort_column="nom", sort_order=True):
        """Charge les aliments dans le tableau avec option de tri"""
        self.table.setSortingEnabled(False)  # Désactiver le tri pendant le chargement

        # Vider le tableau
        self.table.setRowCount(0)

        # Charger les aliments triés
        aliments = self.db_manager.get_aliments(sort_column, sort_order)

        # Remplir le tableau
        self.table.setRowCount(len(aliments))
        for i, aliment in enumerate(aliments):
            # ID (caché)
            id_item = QTableWidgetItem()
            id_item.setData(
                Qt.DisplayRole, aliment["id"]
            )  # Utiliser setData pour stocker en tant que nombre
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
            # Formater le texte avec le symbole €
            if prix_val > 0:
                prix_item.setText(f"{prix_val:.2f} €")
            self.table.setItem(i, 10, prix_item)

        # Réactiver le tri après avoir rempli les données
        self.table.setSortingEnabled(True)

        # Configuration optimisée des largeurs de colonnes
        header = self.table.horizontalHeader()

        # Colonnes à largeur fixe pour un affichage compact mais lisible
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
        }

        # Appliquer les largeurs définies
        for col, width in col_widths.items():
            self.table.setColumnWidth(col, width)
            header.setSectionResizeMode(col, QHeaderView.Interactive)

        # Colonne Nom extensible mais avec limite minimale
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setMinimumSectionSize(100)

        # Ajouter des tooltips aux en-têtes pour plus de clarté
        self.table.horizontalHeaderItem(5).setToolTip("Calories pour 100g")
        self.table.horizontalHeaderItem(6).setToolTip("Protéines en g pour 100g")
        self.table.horizontalHeaderItem(7).setToolTip("Glucides en g pour 100g")
        self.table.horizontalHeaderItem(8).setToolTip("Lipides en g pour 100g")
        self.table.horizontalHeaderItem(9).setToolTip("Fibres en g pour 100g")

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
            self.db_manager.ajouter_aliment(data)
            self.load_data()

    def edit_aliment(self):
        """Modifie l'aliment sélectionné"""
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
            self.load_data()

    def delete_aliment(self):
        """Supprime l'aliment sélectionné"""
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
        aliment_nom = self.table.item(row, 1).text()

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
            self.load_data()

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
