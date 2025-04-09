from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QWidget,
)
from PySide6.QtGui import QColor
from .categorie_dialog import CategorieDialog


class CategoriesManagerDialog(QDialog):
    """Dialogue pour gérer les catégories de repas"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        self.setWindowTitle("Gérer les catégories de repas")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Tableau des catégories
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(3)
        self.categories_table.setHorizontalHeaderLabels(["Nom", "Couleur", "Actions"])
        self.categories_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.categories_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Fixed
        )
        self.categories_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Fixed
        )
        self.categories_table.setColumnWidth(1, 100)
        self.categories_table.setColumnWidth(2, 150)

        layout.addWidget(self.categories_table)

        # Boutons d'action
        buttons_layout = QHBoxLayout()

        self.btn_add = QPushButton("Ajouter une catégorie")
        self.btn_add.clicked.connect(self.add_category)

        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)

        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_close)

        layout.addLayout(buttons_layout)

    def load_categories(self):
        """Charge les catégories dans le tableau"""
        self.categories_table.setRowCount(0)

        categories = self.db_manager.get_categories()

        for i, categorie in enumerate(categories):
            self.categories_table.insertRow(i)

            # Nom
            self.categories_table.setItem(i, 0, QTableWidgetItem(categorie["nom"]))

            # Couleur (avec aperçu)
            color_item = QTableWidgetItem()
            color_item.setBackground(QColor(categorie["couleur"]))
            self.categories_table.setItem(i, 1, color_item)

            # Actions
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)

            btn_edit = QPushButton("Modifier")
            btn_edit.clicked.connect(
                lambda _, id=categorie["id"]: self.edit_category(id)
            )

            btn_delete = QPushButton("Supprimer")
            btn_delete.clicked.connect(
                lambda _, id=categorie["id"], nom=categorie[
                    "nom"
                ]: self.delete_category(id, nom)
            )

            actions_widget = QWidget()
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_delete)
            actions_widget.setLayout(actions_layout)

            self.categories_table.setCellWidget(i, 2, actions_widget)

    def add_category(self):
        """Ajoute une nouvelle catégorie"""
        dialog = CategorieDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            self.db_manager.ajouter_categorie(data["nom"], data["couleur"])
            self.load_categories()

    def edit_category(self, categorie_id):
        """Modifie une catégorie existante"""
        categorie = self.db_manager.get_categorie(categorie_id)
        if not categorie:
            return

        dialog = CategorieDialog(self, categorie)
        if dialog.exec():
            data = dialog.get_data()
            self.db_manager.modifier_categorie(
                categorie_id, data["nom"], data["couleur"]
            )
            self.load_categories()

    def delete_category(self, categorie_id, nom):
        """Supprime une catégorie après confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer la catégorie '{nom}' ?\n\n"
            "Les recettes associées à cette catégorie ne seront pas supprimées, "
            "mais n'auront plus de catégorie.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_categorie(categorie_id)
            self.load_categories()
