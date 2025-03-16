from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QMessageBox,
    QDoubleSpinBox,
    QComboBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMenu,
    QStyledItemDelegate,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from ...utils.events import event_bus


# Délégué personnalisé pour permettre l'édition uniquement de la colonne quantité
class QuantiteDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == 1:  # Colonne quantité uniquement
            editor = QDoubleSpinBox(parent)
            editor.setMinimum(1)
            editor.setMaximum(5000)
            editor.setSuffix(" g")
            return editor
        return None

    def setEditorData(self, editor, index):
        if index.column() == 1:
            value_text = index.model().data(index, Qt.DisplayRole)
            value = float(value_text.replace("g", ""))
            editor.setValue(value)

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            model.setData(index, f"{editor.value()}g", Qt.DisplayRole)

            # Stocker la nouvelle valeur pour mettre à jour la base de données
            aliment_id = index.model().data(index.siblingAtColumn(0), Qt.UserRole)
            nouvelle_quantite = editor.value()

            # Signaler la mise à jour - sera connecté à une méthode dans RecettesTab
            self.parent().quantite_modifiee.emit(aliment_id, nouvelle_quantite)


class RecettesTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_recette_id = None
        self.setup_ui()
        self.load_data()

        # S'abonner aux événements de modification des aliments
        event_bus.aliment_supprime.connect(self.on_aliment_supprime)
        event_bus.aliments_modifies.connect(
            self.refresh_data
        )  # Cette ligne cause l'erreur

    # Signal pour la mise à jour de la quantité
    quantite_modifiee = Signal(int, float)

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Titre
        title = QLabel("<h1>Mes Recettes</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Splitter pour diviser la vue en deux parties
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(
            splitter, 1
        )  # Ajouté stretch factor pour que le splitter prenne tout l'espace disponible

        # Partie gauche : Liste des recettes
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Réduire les marges

        left_layout.addWidget(QLabel("<h3>Liste des recettes</h3>"))

        self.recettes_list = QListWidget()
        self.recettes_list.currentRowChanged.connect(self.afficher_details_recette)
        left_layout.addWidget(
            self.recettes_list, 1
        )  # Ajouté stretch factor pour que la liste prenne l'espace vertical

        # Boutons d'action pour les recettes
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Nouvelle recette")
        self.btn_add.clicked.connect(self.ajouter_recette)
        self.btn_edit = QPushButton("Modifier")
        self.btn_edit.clicked.connect(self.modifier_recette)
        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.clicked.connect(self.supprimer_recette)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)

        left_layout.addLayout(btn_layout)

        # Partie droite : Détails de la recette
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)  # Réduire les marges
        self.right_layout.setSpacing(10)  # Meilleur espacement entre les éléments

        self.detail_titre = QLabel("<h3>Détails de la recette</h3>")
        self.right_layout.addWidget(self.detail_titre)

        # Remplacer le QLabel par un QTextEdit pour la description, pour permettre le défilement
        self.detail_description = QTextEdit()
        self.detail_description.setReadOnly(True)
        self.detail_description.setPlaceholderText(
            "Sélectionnez une recette pour voir ses détails."
        )
        self.detail_description.setMaximumHeight(
            100
        )  # Limiter la hauteur pour ne pas prendre trop de place
        self.right_layout.addWidget(self.detail_description)

        # Configuration du tableau des ingrédients
        self.right_layout.addWidget(QLabel("<h4>Ingrédients</h4>"))

        self.detail_ingredients = QTableWidget()
        self.detail_ingredients.setColumnCount(5)
        self.detail_ingredients.setHorizontalHeaderLabels(
            ["Aliment", "Quantité (g)", "Calories", "Macros", "Actions"]
        )

        # Configuration des colonnes
        self.detail_ingredients.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.detail_ingredients.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.detail_ingredients.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.detail_ingredients.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )
        self.detail_ingredients.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )

        # Définir une hauteur minimale pour le tableau
        self.detail_ingredients.setMinimumHeight(200)
        self.right_layout.addWidget(
            self.detail_ingredients, 3
        )  # Grande priorité de stretch

        # Configurer l'édition limitée à la colonne quantité
        self.quantite_delegate = QuantiteDelegate(self)
        self.detail_ingredients.setItemDelegate(self.quantite_delegate)
        self.detail_ingredients.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed
        )

        # Connecter le signal de modification de quantité
        self.quantite_modifiee.connect(self.update_ingredient_quantite)

        # Permettre le menu contextuel
        self.detail_ingredients.setContextMenuPolicy(Qt.CustomContextMenu)
        self.detail_ingredients.customContextMenuRequested.connect(
            self.show_ingredient_context_menu
        )

        self.detail_nutrition = QLabel(
            "Valeurs nutritionnelles de la recette sélectionnée"
        )
        self.right_layout.addWidget(QLabel("<h4>Valeurs nutritionnelles</h4>"))
        self.right_layout.addWidget(self.detail_nutrition)

        # Bouton pour ajouter un ingrédient à la recette sélectionnée
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)  # Marge en haut pour l'espacement

        self.btn_add_ingredient = QPushButton("Ajouter un ingrédient")
        self.btn_add_ingredient.clicked.connect(self.ajouter_ingredient)
        button_layout.addWidget(self.btn_add_ingredient)
        self.right_layout.addWidget(button_container)

        # Ajouter un stretch en bas pour que tout reste en haut
        self.right_layout.addStretch(1)

        # Ajouter les widgets au splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])

        self.setLayout(main_layout)

    def load_data(self):
        """Charge la liste des repas types"""
        self.recettes_list.clear()
        repas_types = self.db_manager.get_repas_types()

        for repas_type in repas_types:
            item = QListWidgetItem(repas_type["nom"])
            item.setData(Qt.UserRole, repas_type["id"])
            self.recettes_list.addItem(item)

    def afficher_details_recette(self, row):
        """Affiche les détails de la recette sélectionnée"""
        # Nettoyer l'affichage actuel
        self.detail_nutrition.setText("")
        self.detail_ingredients.setRowCount(0)

        if row < 0:
            # Réinitialiser les widgets quand rien n'est sélectionné
            self.detail_titre.setText("<h3>Détails de la recette</h3>")
            self.detail_description.setPlainText(
                ""
            )  # Utiliser setPlainText au lieu de setText
            return

        recette_id = self.recettes_list.item(row).data(Qt.UserRole)
        self.current_recette_id = recette_id  # Stocker l'ID de la recette sélectionnée
        recette = self.db_manager.get_repas_type(recette_id)

        # Mettre à jour les détails
        self.detail_titre.setText(f"<h3>{recette['nom']}</h3>")

        # Afficher la description complète dans le QTextEdit
        description = recette["description"] or ""
        self.detail_description.setPlainText(description)

        # Effacer et remplir le tableau d'ingrédients
        self.detail_ingredients.setRowCount(0)

        # Stocker les IDs des aliments pour l'édition de quantité
        self.aliment_ids = []

        for i, aliment in enumerate(recette["aliments"]):
            self.detail_ingredients.insertRow(i)
            nom_item = QTableWidgetItem(aliment["nom"])
            nom_item.setData(Qt.UserRole, aliment["id"])  # Stocker l'ID
            self.detail_ingredients.setItem(i, 0, nom_item)

            # Quantité - éditable
            quantite_item = QTableWidgetItem(f"{aliment['quantite']}g")
            quantite_item.setData(Qt.UserRole, aliment["id"])  # Stocker l'ID
            self.detail_ingredients.setItem(i, 1, quantite_item)

            # Ajouter l'ID à la liste
            self.aliment_ids.append(aliment["id"])

            # Calories
            calories = aliment["calories"] * aliment["quantite"] / 100
            self.detail_ingredients.setItem(
                i, 2, QTableWidgetItem(f"{calories:.0f} kcal")
            )

            # Macros
            macros = f"P: {aliment['proteines'] * aliment['quantite'] / 100:.1f}g | "
            macros += f"G: {aliment['glucides'] * aliment['quantite'] / 100:.1f}g | "
            macros += f"L: {aliment['lipides'] * aliment['quantite'] / 100:.1f}g"
            self.detail_ingredients.setItem(i, 3, QTableWidgetItem(macros))

            # Bouton de suppression (croix rouge) - version améliorée
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)  # Réduire les marges
            btn_layout.setAlignment(Qt.AlignCenter)  # Centrer dans la cellule

            btn_delete = QPushButton("×")
            btn_delete.setFixedSize(16, 16)  # Taille réduite et carrée
            btn_delete.setStyleSheet(
                """
              QPushButton {
                color: white;
                background-color: #e74c3c;
                font-weight: bold;
                font-size: 14px;
                padding: 0px;
                margin: 0px;
              }
              QPushButton:hover {
                background-color: #c0392b;
              }
              """
            )
            btn_delete.setToolTip("Supprimer cet ingrédient")
            btn_delete.clicked.connect(
                lambda checked, aid=aliment["id"]: self.supprimer_ingredient(aid)
            )

            btn_layout.addWidget(btn_delete)
            self.detail_ingredients.setCellWidget(i, 4, btn_container)

            # Stocker l'ID de l'aliment dans l'élément
            for col in range(4):
                if self.detail_ingredients.item(i, col):
                    self.detail_ingredients.item(i, col).setData(
                        Qt.UserRole, aliment["id"]
                    )

        # Afficher les valeurs nutritionnelles totales
        nutrition = f"<b>Calories:</b> {recette['total_calories']:.0f} kcal<br>"
        nutrition += f"<b>Protéines:</b> {recette['total_proteines']:.1f}g<br>"
        nutrition += f"<b>Glucides:</b> {recette['total_glucides']:.1f}g<br>"
        nutrition += f"<b>Lipides:</b> {recette['total_lipides']:.1f}g"
        self.detail_nutrition.setText(nutrition)

    def ajouter_recette(self):
        """Ajoute une nouvelle recette"""
        dialog = RecetteDialog(self)
        if dialog.exec():
            nom, description = dialog.get_data()
            self.db_manager.ajouter_repas_type(nom, description)
            self.load_data()

    def supprimer_recette(self):
        """Supprime la recette sélectionnée"""
        current_row = self.recettes_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner une recette à supprimer.",
            )
            return

        recette_id = self.recettes_list.item(current_row).data(Qt.UserRole)
        recette_nom = self.recettes_list.item(current_row).text()

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer la recette '{recette_nom}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_repas_type(recette_id)
            self.load_data()

    def ajouter_ingredient(self):
        """Ajoute un ingrédient à la recette sélectionnée"""
        current_row = self.recettes_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "Sélection requise", "Veuillez sélectionner une recette."
            )
            return

        recette_id = self.recettes_list.item(current_row).data(Qt.UserRole)

        dialog = IngredientRecetteDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()
            self.db_manager.ajouter_aliment_repas_type(recette_id, aliment_id, quantite)
            self.afficher_details_recette(current_row)

    def appliquer_au_planning(self):
        """Applique la recette sélectionnée au planning"""
        current_row = self.recettes_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self, "Sélection requise", "Veuillez sélectionner une recette."
            )
            return

        recette_id = self.recettes_list.item(current_row).data(Qt.UserRole)

        dialog = AppliquerRecetteDialog(self)
        if dialog.exec():
            jour, ordre = dialog.get_data()
            self.db_manager.appliquer_repas_type_au_jour(recette_id, jour, ordre)
            QMessageBox.information(
                self,
                "Recette appliquée",
                "La recette a été ajoutée au planning avec succès.",
            )

    def supprimer_ingredient(self, aliment_id):
        """Supprime un ingrédient de la recette"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet ingrédient de la recette ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Ajouter cette méthode à db_manager.py
            self.db_manager.supprimer_aliment_repas_type(
                self.current_recette_id, aliment_id
            )

            # Rafraîchir l'affichage
            current_row = self.recettes_list.currentRow()
            self.afficher_details_recette(current_row)

    def show_ingredient_context_menu(self, position):
        """Affiche un menu contextuel pour les actions sur les ingrédients"""
        item = self.detail_ingredients.itemAt(position)
        if item:
            aliment_id = item.data(Qt.UserRole)
            menu = QMenu(self)
            action_supprimer = menu.addAction("Supprimer de la recette")
            action = menu.exec_(QCursor.pos())
            if action == action_supprimer:
                self.supprimer_ingredient(aliment_id)

    def update_ingredient_quantite(self, aliment_id, nouvelle_quantite):
        """Met à jour la quantité d'un ingrédient dans la recette"""
        if self.current_recette_id is None:
            return

        # Mettre à jour la base de données
        self.db_manager.modifier_quantite_aliment_repas_type(
            self.current_recette_id, aliment_id, nouvelle_quantite
        )

        # Rafraîchir l'affichage pour mettre à jour les calories et macros
        current_row = self.recettes_list.currentRow()
        self.afficher_details_recette(current_row)

        # Afficher un message de confirmation
        QMessageBox.information(
            self, "Quantité mise à jour", f"La quantité a été modifiée avec succès."
        )

    def modifier_recette(self):
        """Modifie la recette sélectionnée"""
        current_row = self.recettes_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                "Sélection requise",
                "Veuillez sélectionner une recette à modifier.",
            )
            return

        recette_id = self.recettes_list.item(current_row).data(Qt.UserRole)

        # Récupérer les informations de la recette
        recette = self.db_manager.get_repas_type(recette_id)

        # Créer un dialogue de modification avec les données pré-remplies
        dialog = RecetteDialog(self, recette)
        if dialog.exec():
            nom, description = dialog.get_data()

            # Mettre à jour la base de données
            self.db_manager.modifier_repas_type(recette_id, nom, description)

            # Recharger les données
            self.load_data()

            # Réafficher les détails de la recette modifiée
            for i in range(self.recettes_list.count()):
                if self.recettes_list.item(i).data(Qt.UserRole) == recette_id:
                    self.recettes_list.setCurrentRow(i)
                    break

    def on_aliment_supprime(self, aliment_id):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir les recettes qui pourraient contenir cet aliment
        self.refresh_data()

    # Ajout de la méthode manquante
    def refresh_data(self):
        """Rafraîchit les données affichées"""
        current_row = self.recettes_list.currentRow()
        self.load_data()

        # Restaurer la sélection si possible
        if current_row >= 0 and current_row < self.recettes_list.count():
            self.recettes_list.setCurrentRow(current_row)
        elif self.recettes_list.count() > 0:
            self.recettes_list.setCurrentRow(0)


class RecetteDialog(QDialog):
    """Dialogue pour ajouter ou modifier une recette"""

    def __init__(self, parent=None, recette=None):
        super().__init__(parent)
        self.recette = recette
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(
            "Nouvelle recette" if not self.recette else "Modifier la recette"
        )
        self.setMinimumWidth(400)

        layout = QFormLayout()

        # Nom de la recette
        self.nom_input = QLineEdit()
        if self.recette:
            self.nom_input.setText(self.recette["nom"])
        layout.addRow("Nom de la recette *:", self.nom_input)

        # Description
        self.description_input = QTextEdit()
        if self.recette:
            self.description_input.setText(self.recette["description"])
        self.description_input.setPlaceholderText(
            "Notes, instructions de préparation..."
        )
        layout.addRow("Description:", self.description_input)

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
        if not self.nom_input.text().strip():
            QMessageBox.warning(
                self, "Champ obligatoire", "Le nom de la recette est obligatoire."
            )
            return

        self.accept()

    def get_data(self):
        return (
            self.nom_input.text().strip(),
            self.description_input.toPlainText().strip(),
        )


class IngredientRecetteDialog(QDialog):
    """Dialogue pour ajouter un ingrédient à une recette"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un ingrédient à la recette")
        self.setMinimumWidth(
            450
        )  # Augmenter la largeur minimale pour éviter la troncature

        layout = QFormLayout()

        # Sélection de l'aliment
        self.aliment_combo = QComboBox()
        self.load_aliments()
        layout.addRow("Aliment:", self.aliment_combo)

        # Quantité en grammes avec signal pour mise à jour des macros
        self.quantite_input = QDoubleSpinBox()
        self.quantite_input.setMinimum(1)
        self.quantite_input.setMaximum(5000)
        self.quantite_input.setValue(100)
        self.quantite_input.setSuffix(" g")
        self.quantite_input.valueChanged.connect(self.update_info)
        layout.addRow("Quantité:", self.quantite_input)

        # Supprimer le label d'info pour les macros au 100g et garder seulement les macros proportionnelles
        # self.info_label = QLabel("Sélectionnez un aliment pour voir ses informations")
        # layout.addRow(self.info_label)

        # Label pour afficher les macros proportionnellement au poids
        self.macros_label = QLabel("")
        self.macros_label.setWordWrap(True)  # Permettre le retour à la ligne
        layout.addRow("", self.macros_label)

        # Mettre à jour les informations quand on change d'aliment
        self.aliment_combo.currentIndexChanged.connect(self.update_info)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Ajouter")
        self.btn_save.clicked.connect(self.accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def load_aliments(self):
        aliments = self.db_manager.get_aliments(sort_column="nom", sort_order=True)
        self.aliment_ids = [aliment["id"] for aliment in aliments]

        for aliment in aliments:
            self.aliment_combo.addItem(
                f"{aliment['nom']} ({aliment['marque'] or 'Sans marque'})"
            )

    def update_info(self):
        if self.aliment_combo.currentIndex() >= 0:
            aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
            aliment = self.db_manager.get_aliment(aliment_id)
            quantite = self.quantite_input.value()

            # Supprimer l'affichage des infos par 100g
            # info_text = f"<b>Calories:</b> {aliment['calories']} kcal/100g | "
            # info_text += f"<b>P:</b> {aliment['proteines']}g | "
            # info_text += f"<b>G:</b> {aliment['glucides']}g | "
            # info_text += f"<b>L:</b> {aliment['lipides']}g"
            # self.info_label.setText(info_text)

            # Information proportionnelle au poids
            ratio = quantite / 100.0
            macro_text = f"<b>Calories:</b> {aliment['calories'] * ratio:.0f} kcal<br>"
            macro_text += f"<b>Protéines:</b> {aliment['proteines'] * ratio:.1f}g<br>"
            macro_text += f"<b>Glucides:</b> {aliment['glucides'] * ratio:.1f}g<br>"
            macro_text += f"<b>Lipides:</b> {aliment['lipides'] * ratio:.1f}g"
            self.macros_label.setText(macro_text)

    def get_data(self):
        aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
        return (aliment_id, self.quantite_input.value())


class AppliquerRecetteDialog(QDialog):
    """Dialogue pour appliquer une recette au planning"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Appliquer la recette au planning")
        self.setMinimumWidth(300)

        layout = QFormLayout()

        # Sélection du jour
        self.jour_input = QComboBox()
        self.jour_input.addItems(
            ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        )
        layout.addRow("Jour:", self.jour_input)

        # Ordre dans la journée
        self.ordre_input = QSpinBox()
        self.ordre_input.setMinimum(1)
        self.ordre_input.setValue(1)
        layout.addRow("Position dans la journée:", self.ordre_input)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Appliquer")
        self.btn_save.clicked.connect(self.accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return (
            self.jour_input.currentText(),
            self.ordre_input.value(),
        )
