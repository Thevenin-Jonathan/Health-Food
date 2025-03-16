from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QLabel,
    QDoubleSpinBox,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor

from ..dialogs.ajouter_aliment_dialog import AjouterAlimentDialog


class AlimentsTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_sort_column = None
        self.sort_order = True  # True pour ASC, False pour DESC
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Tableau des aliments
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "Nom",
                "Marque",
                "Magasin",
                "Catégorie",
                "Calories",
                "Protéines (g)",
                "Glucides (g)",
                "Lipides (g)",
                "Fibres (g)",
                "Prix/kg (€)",
            ]
        )

        # Permettre le tri en cliquant sur les en-têtes
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.setSortingEnabled(False)  # Désactiver le tri automatique du tableau
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        # Boutons d'action
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("Ajouter un aliment")
        self.btn_add.clicked.connect(self.add_aliment)

        self.btn_edit = QPushButton("Modifier")
        self.btn_edit.clicked.connect(self.edit_aliment)

        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.clicked.connect(self.delete_aliment)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_data(self):
        # Effacer le tableau
        self.table.setRowCount(0)

        # Récupérer les aliments triés si nécessaire
        aliments = self.db_manager.get_aliments(
            self.current_sort_column, self.sort_order
        )

        # Remplir le tableau
        for row, aliment in enumerate(aliments):
            self.table.insertRow(row)

            # Nom (texte)
            self.table.setItem(row, 0, QTableWidgetItem(aliment["nom"]))

            # Marque (texte)
            self.table.setItem(row, 1, QTableWidgetItem(aliment["marque"] or ""))

            # Magasin (texte)
            self.table.setItem(row, 2, QTableWidgetItem(aliment["magasin"] or ""))

            # Catégorie (texte)
            self.table.setItem(row, 3, QTableWidgetItem(aliment["categorie"] or ""))

            # Calories (nombre)
            calories_item = QTableWidgetItem()
            calories_item.setData(Qt.DisplayRole, aliment["calories"] or 0)
            self.table.setItem(row, 4, calories_item)

            # Protéines (nombre)
            proteines_item = QTableWidgetItem()
            proteines_item.setData(Qt.DisplayRole, aliment["proteines"] or 0)
            self.table.setItem(row, 5, proteines_item)

            # Glucides (nombre)
            glucides_item = QTableWidgetItem()
            glucides_item.setData(Qt.DisplayRole, aliment["glucides"] or 0)
            self.table.setItem(row, 6, glucides_item)

            # Lipides (nombre)
            lipides_item = QTableWidgetItem()
            lipides_item.setData(Qt.DisplayRole, aliment["lipides"] or 0)
            self.table.setItem(row, 7, lipides_item)

            # Fibres (nombre)
            fibres_item = QTableWidgetItem()
            fibres_item.setData(Qt.DisplayRole, aliment["fibres"] or 0)
            self.table.setItem(row, 8, fibres_item)

            # Prix/kg (nombre)
            prix_item = QTableWidgetItem()
            prix_item.setData(Qt.DisplayRole, aliment["prix_kg"] or 0)
            self.table.setItem(row, 9, prix_item)

            # Stocker l'ID comme données
            self.table.item(row, 0).setData(Qt.UserRole, aliment["id"])

    def on_header_clicked(self, index):
        # Mapping des index de colonnes vers les noms de colonnes de la base de données
        column_mapping = {
            0: "nom",
            1: "marque",
            2: "magasin",
            3: "categorie",
            4: "calories",
            5: "proteines",
            6: "glucides",
            7: "lipides",
            8: "fibres",
            9: "prix_kg",
        }

        column_name = column_mapping.get(index)

        # Si c'est la même colonne, inverser l'ordre
        if self.current_sort_column == column_name:
            self.sort_order = not self.sort_order
        else:
            self.current_sort_column = column_name
            self.sort_order = True

        # Mettre à jour l'indicateur visuel de tri
        self.table.horizontalHeader().setSortIndicator(
            index, Qt.AscendingOrder if self.sort_order else Qt.DescendingOrder
        )

        # Actualiser les données avec le tri approprié
        self.load_data()

    def add_aliment(self):
        dialog = AjouterAlimentDialog(self, self.db_manager)
        if dialog.exec():
            data = dialog.get_data()
            # Ajouter les valeurs par défaut pour les champs non requis
            if "categorie" not in data or not data["categorie"]:
                data["categorie"] = None
            if "fibres" not in data:
                data["fibres"] = None
            if "prix_kg" not in data:
                data["prix_kg"] = None

            aliment_id = self.db_manager.ajouter_aliment(data)
            self.charger_aliments()
            self.select_aliment(
                aliment_id
            )  # Sélectionner l'aliment nouvellement ajouté
            return True
        return False

    def edit_aliment(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner un aliment à modifier.",
            )
            return

        # Récupérer l'ID de l'aliment sélectionné
        row = selected_items[0].row()
        aliment_id = self.table.item(row, 0).data(Qt.UserRole)

        # Récupérer les données actuelles
        aliment = self.db_manager.get_aliment(aliment_id)

        # Ouvrir la boîte de dialogue avec les données pré-remplies
        dialog = AlimentDialog(self, aliment)
        if dialog.exec():
            data = dialog.get_data()
            self.db_manager.modifier_aliment(aliment_id, data)
            self.load_data()

    def delete_aliment(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner un aliment à supprimer.",
            )
            return

        # Confirmer la suppression
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet aliment ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            row = selected_items[0].row()
            aliment_id = self.table.item(row, 0).data(Qt.UserRole)
            self.db_manager.supprimer_aliment(aliment_id)
            self.load_data()


class AlimentDialog(QDialog):
    def __init__(self, parent=None, aliment=None):
        super().__init__(parent)
        self.aliment = aliment
        self.setup_ui()

    def setup_ui(self):
        if self.aliment:
            self.setWindowTitle("Modifier un aliment")
        else:
            self.setWindowTitle("Ajouter un aliment")

        self.setMinimumWidth(400)
        layout = QFormLayout()

        # Champs de saisie
        self.nom_input = QLineEdit()
        self.marque_input = QLineEdit()
        self.magasin_input = QLineEdit()
        self.categorie_input = QComboBox()

        # Catégories prédéfinies
        categories = [
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
            "Autre",
        ]
        self.categorie_input.addItems(categories)
        self.categorie_input.setEditable(True)

        self.calories_input = QDoubleSpinBox()
        self.calories_input.setMaximum(1000)

        self.proteines_input = QDoubleSpinBox()
        self.proteines_input.setMaximum(100)

        self.glucides_input = QDoubleSpinBox()
        self.glucides_input.setMaximum(100)

        self.lipides_input = QDoubleSpinBox()
        self.lipides_input.setMaximum(100)

        self.fibres_input = QDoubleSpinBox()
        self.fibres_input.setMaximum(100)

        self.prix_input = QDoubleSpinBox()
        self.prix_input.setMaximum(1000)
        self.prix_input.setSuffix(" €/kg")

        # Pré-remplir les champs si on modifie un aliment existant
        if self.aliment:
            self.nom_input.setText(self.aliment["nom"])
            self.marque_input.setText(self.aliment["marque"] or "")
            self.magasin_input.setText(self.aliment["magasin"] or "")

            # Chercher si la catégorie existe déjà, sinon l'ajouter
            categorie = self.aliment["categorie"] or ""
            if categorie:
                index = self.categorie_input.findText(categorie)
                if index >= 0:
                    self.categorie_input.setCurrentIndex(index)
                else:
                    self.categorie_input.addItem(categorie)
                    self.categorie_input.setCurrentText(categorie)

            self.calories_input.setValue(self.aliment["calories"] or 0)
            self.proteines_input.setValue(self.aliment["proteines"] or 0)
            self.glucides_input.setValue(self.aliment["glucides"] or 0)
            self.lipides_input.setValue(self.aliment["lipides"] or 0)
            self.fibres_input.setValue(self.aliment["fibres"] or 0)
            self.prix_input.setValue(self.aliment["prix_kg"] or 0)

        # Ajouter les champs au formulaire
        layout.addRow("Nom *:", self.nom_input)
        layout.addRow("Marque:", self.marque_input)
        layout.addRow("Magasin:", self.magasin_input)
        layout.addRow("Catégorie:", self.categorie_input)
        layout.addRow("Calories (pour 100g):", self.calories_input)
        layout.addRow("Protéines (g/100g):", self.proteines_input)
        layout.addRow("Glucides (g/100g):", self.glucides_input)
        layout.addRow("Lipides (g/100g):", self.lipides_input)
        layout.addRow("Fibres (g/100g):", self.fibres_input)
        layout.addRow("Prix au kilo (€):", self.prix_input)

        # Note explicative
        note = QLabel("* Champ obligatoire")
        layout.addRow(note)

        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.validate_and_accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)

        layout.addRow(btn_layout)
        self.setLayout(layout)

    def validate_and_accept(self):
        # Vérifier que le nom n'est pas vide
        if not self.nom_input.text().strip():
            QMessageBox.warning(
                self, "Champ obligatoire", "Le nom de l'aliment est obligatoire."
            )
            return

        self.accept()

    def get_data(self):
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
            "prix_kg": self.prix_input.value(),
        }
