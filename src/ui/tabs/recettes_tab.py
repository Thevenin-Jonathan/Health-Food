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
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QColor
from src.utils.events import EVENT_BUS
from src.ui.dialogs.categories_manager_dialog import CategoriesManagerDialog


# Délégué personnalisé pour permettre l'édition uniquement de la colonne quantité
class QuantiteDelegate(QStyledItemDelegate):
    # pylint: disable=invalid-name
    # pylint: disable=unused-argument
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
        self.setObjectName("RecettesTab")
        self.current_recette_id = None
        self.setup_ui()
        self.load_data()

        # S'abonner aux événements de modification des aliments
        EVENT_BUS.aliment_supprime.connect(self.on_aliment_supprime)
        EVENT_BUS.aliments_modifies.connect(
            self.refresh_data
        )  # Cette ligne cause l'erreur

    # Signal pour la mise à jour de la quantité
    quantite_modifiee = Signal(int, float)

    def setup_ui(self):
        self.aliment_ids = []

        # Créer un layout principal sans marges pour le widget entier
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Créer un layout horizontal pour centrer le contenu
        center_layout = QHBoxLayout()

        # Créer un widget contenant le contenu réel avec sa largeur limitée
        content_widget = QWidget()
        content_widget.setMaximumWidth(
            1200
        )  # Largeur maximale plus grande pour les tableaux
        content_widget.setMinimumWidth(
            900
        )  # Largeur minimale pour garantir la lisibilité

        # Layout principal du contenu
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        title = QLabel("<h1>Mes repas</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Splitter pour diviser la vue en deux parties
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(
            splitter, 1
        )  # Stretch factor pour que le splitter prenne tout l'espace disponible

        # Partie gauche : Liste des repas
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Réduire les marges

        left_title = QLabel("<h3>Liste des repas</h3>")
        left_title.setProperty("class", "section-title")
        left_layout.addWidget(left_title)

        # Ajouter un panneau de filtrage au-dessus de la liste des recettes
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 10)
        filter_layout.setSpacing(5)

        # Filtre de recherche (ligne 1)
        search_container = QHBoxLayout()
        search_container.setContentsMargins(0, 0, 0, 0)
        search_label = QLabel("Recherche:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une recette...")
        self.search_input.textChanged.connect(self.apply_filters)
        search_container.addWidget(search_label)
        search_container.addWidget(self.search_input)
        filter_layout.addLayout(search_container)

        # Filtre par catégorie (ligne 2)
        category_container = QHBoxLayout()
        category_container.setContentsMargins(0, 0, 0, 0)
        category_label = QLabel("Catégorie:")
        self.category_filter = QComboBox()
        self.category_filter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.category_filter.addItem("Toutes les catégories", None)
        self.category_filter.currentIndexChanged.connect(self.apply_filters)

        # Bouton pour gérer les catégories
        self.btn_manage_categories = QPushButton("Gérer")
        self.btn_manage_categories.setToolTip("Gérer les catégories")
        self.btn_manage_categories.clicked.connect(self.manage_categories)
        self.btn_manage_categories.setMaximumWidth(60)  # Limiter la largeur du bouton

        category_container.addWidget(category_label)
        category_container.addWidget(self.category_filter)
        category_container.addWidget(self.btn_manage_categories)
        filter_layout.addLayout(category_container)

        # Ajouter à votre layout existant
        left_layout.insertWidget(1, filter_widget)  # Insérer juste après left_title

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
        self.btn_delete.setObjectName("cancelButton")
        self.btn_delete.clicked.connect(self.supprimer_recette)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)

        left_layout.addLayout(btn_layout)

        # Partie droite : Détails du repas
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)  # Réduire les marges
        self.right_layout.setSpacing(10)  # Meilleur espacement entre les éléments

        self.detail_titre = QLabel("<h3>Détails du repas</h3>")
        self.detail_titre.setProperty("class", "section-title")
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
        self.detail_ingredients = QTableWidget()
        self.detail_ingredients.setObjectName("ingredientsTable")
        self.detail_ingredients.setColumnCount(5)
        self.detail_ingredients.setHorizontalHeaderLabels(
            ["Aliment", "Quantité (g)", "Calories", "Macros", "Actions"]
        )

        # Optimisation de l'espace dans le tableau
        self.detail_ingredients.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Configuration des colonnes pour l'espace limité
        header = self.detail_ingredients.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Aliment
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Quantité
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Calories
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Macros
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Actions

        self.detail_ingredients.verticalHeader().setVisible(
            False
        )  # Masquer les en-têtes de ligne verticaux

        # Définir des largeurs fixes pour les colonnes non élastiques
        self.detail_ingredients.setColumnWidth(1, 90)  # Quantité
        self.detail_ingredients.setColumnWidth(2, 80)  # Calories
        self.detail_ingredients.setColumnWidth(3, 180)  # Macros
        self.detail_ingredients.setColumnWidth(4, 70)  # Actions

        # Définir une hauteur minimale pour le tableau
        self.detail_ingredients.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.detail_ingredients.setMinimumHeight(200)
        self.right_layout.addWidget(self.detail_ingredients)

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

        # Désactiver la sélection de cellules individuelles
        self.detail_ingredients.setSelectionMode(QTableWidget.NoSelection)
        self.detail_ingredients.setFocusPolicy(Qt.NoFocus)  # Évite le focus du tableau

        # Ajouter un titre pour la section des valeurs nutritionnelles
        nutrition_title = QLabel("<h4>Valeurs nutritionnelles</h4>")
        nutrition_title.setProperty("class", "subsection-title")
        self.right_layout.addWidget(nutrition_title)

        # Créer un conteneur stylisé pour les valeurs nutritionnelles
        nutrition_container = QFrame()
        nutrition_container.setObjectName("nutritionFrame")
        nutrition_container.setProperty("class", "nutrition-summary")
        nutrition_layout = QHBoxLayout(nutrition_container)

        # Créer quatre sections pour les macronutriments principaux
        self.calories_label = QLabel("0 kcal")
        self.calories_label.setAlignment(Qt.AlignCenter)
        self.calories_label.setProperty("class", "nutrition-value")

        self.proteines_label = QLabel("0g")
        self.proteines_label.setAlignment(Qt.AlignCenter)
        self.proteines_label.setProperty("class", "nutrition-value")

        self.glucides_label = QLabel("0g")
        self.glucides_label.setAlignment(Qt.AlignCenter)
        self.glucides_label.setProperty("class", "nutrition-value")

        self.lipides_label = QLabel("0g")
        self.lipides_label.setAlignment(Qt.AlignCenter)
        self.lipides_label.setProperty("class", "nutrition-value")

        # Créer des conteneurs individuels pour chaque macro avec icône/titre
        calories_widget = self.create_nutrition_widget("Calories", self.calories_label)
        proteines_widget = self.create_nutrition_widget(
            "Protéines", self.proteines_label
        )
        glucides_widget = self.create_nutrition_widget("Glucides", self.glucides_label)
        lipides_widget = self.create_nutrition_widget("Lipides", self.lipides_label)

        # Ajouter les widgets au layout
        nutrition_layout.addWidget(calories_widget)
        nutrition_layout.addWidget(proteines_widget)
        nutrition_layout.addWidget(glucides_widget)
        nutrition_layout.addWidget(lipides_widget)

        # Ajouter le conteneur au layout principal
        self.right_layout.addWidget(nutrition_container)

        # Bouton pour ajouter un ingrédient à la recette sélectionnée
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)  # Marge en haut pour l'espacement

        self.btn_add_ingredient = QPushButton("Ajouter un ingrédient")
        self.btn_add_ingredient.clicked.connect(self.ajouter_ingredient)
        button_layout.addWidget(self.btn_add_ingredient)
        self.right_layout.addWidget(button_container)

        # Ajouter les widgets au splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])  # Proportions initiales

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

        self.setLayout(outer_layout)

    def load_data(self):
        """Charge la liste des repas types"""
        # Charger les catégories d'abord
        self.load_categories()

        # Appliquer les filtres (qui chargera aussi les recettes)
        self.apply_filters()

    def load_categories(self):
        """Charge les catégories dans le filtre"""
        self.category_filter.clear()
        self.category_filter.addItem("Toutes les catégories", None)

        categories = self.db_manager.get_categories()
        for categorie in categories:
            self.category_filter.addItem(categorie["nom"], categorie["id"])

    def apply_filters(self):
        """Applique les filtres et charge les données"""
        self.recettes_list.clear()

        # Obtenir les valeurs des filtres
        categorie_id = self.category_filter.currentData()
        recherche = self.search_input.text().strip()

        # Récupérer les recettes filtrées
        repas_types = self.db_manager.get_repas_types_filtres(categorie_id, recherche)

        for repas_type in repas_types:
            # Créer l'item avec formatage conditionnel pour les catégories
            item = QListWidgetItem(repas_type["nom"])
            item.setData(Qt.UserRole, repas_type["id"])

            # Si le repas a une catégorie, lui appliquer une couleur
            if repas_type.get("categorie_id"):
                categorie = self.db_manager.get_categorie(repas_type["categorie_id"])
                if categorie:
                    item.setBackground(QColor(categorie["couleur"]))
                    # Assurez-vous que le texte reste lisible
                    item.setForeground(
                        QColor(
                            "white"
                            if self.is_dark_color(categorie["couleur"])
                            else "black"
                        )
                    )

            self.recettes_list.addItem(item)

    def is_dark_color(self, color):
        """Détermine si une couleur est sombre pour choisir le texte contrastant"""
        # Convertit la couleur hexadécimale en RGB
        color = color.lstrip("#")
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        # Formule de luminosité approximative
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5  # Si < 0.5, considéré comme sombre

    def manage_categories(self):
        """Ouvre un dialogue pour gérer les catégories"""
        dialog = CategoriesManagerDialog(self, self.db_manager)
        if dialog.exec():
            # Recharger les catégories et appliquer les filtres
            self.load_categories()
            self.apply_filters()

    def afficher_details_recette(self, row):
        """Affiche les détails du repas sélectionné"""
        self.calories_label.setText("0 kcal")
        self.proteines_label.setText("0g")
        self.glucides_label.setText("0g")
        self.lipides_label.setText("0g")
        self.detail_ingredients.setRowCount(0)

        if row < 0:
            # Réinitialiser les widgets quand rien n'est sélectionné
            self.detail_titre.setText("<h3>Détails du repas</h3>")
            self.detail_description.setPlainText(
                ""
            )  # Utiliser setPlainText au lieu de setText
            return

        recette_id = self.recettes_list.item(row).data(Qt.UserRole)
        self.current_recette_id = recette_id  # Stocker l'ID de la recette sélectionnée
        recette = self.db_manager.get_repas_type(recette_id)

        # Mettre à jour les détails
        self.detail_titre.setText(f"<h3>{recette['nom']}</h3>")

        # Créer une ligne d'info avec portions et temps
        info_text = ""
        if "nb_portions" in recette and recette["nb_portions"] > 0:
            info_text += f"<b>Portions:</b> {recette['nb_portions']} "

        if "temps_preparation" in recette and recette["temps_preparation"] > 0:
            if info_text:
                info_text += " | "
            info_text += f"<b>Préparation:</b> {recette['temps_preparation']} min"

        if "temps_cuisson" in recette and recette["temps_cuisson"] > 0:
            if info_text:
                info_text += " | "
            info_text += f"<b>Cuisson:</b> {recette['temps_cuisson']} min"

        if info_text:
            info_label = QLabel(info_text)
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setProperty("class", "recipe-info")

            # Si un ancien label d'info existe, le remplacer
            old_info = self.findChild(QLabel, "recipe-info-label")
            if old_info:
                self.right_layout.removeWidget(old_info)
                old_info.deleteLater()

            info_label.setObjectName("recipe-info-label")
            self.right_layout.insertWidget(
                2, info_label
            )  # Après le titre et avant la description

        # Afficher la description complète dans le QTextEdit
        description = recette["description"] or ""
        self.detail_description.setPlainText(description)

        # Effacer et remplir le tableau d'ingrédients
        self.detail_ingredients.setRowCount(0)

        for i, aliment in enumerate(recette["aliments"]):
            self.detail_ingredients.insertRow(i)
            nom_item = QTableWidgetItem(aliment["nom"])
            nom_item.setData(Qt.UserRole, aliment["id"])  # Stocker l'ID
            nom_item.setFlags(nom_item.flags() & ~Qt.ItemIsSelectable)
            self.detail_ingredients.setItem(i, 0, nom_item)

            # Quantité - éditable
            quantite_item = QTableWidgetItem(f"{aliment['quantite']}g")
            quantite_item.setData(Qt.UserRole, aliment["id"])  # Stocker l'ID
            quantite_item.setTextAlignment(Qt.AlignCenter)  # Centrer le texte
            quantite_item.setFlags(
                (quantite_item.flags() | Qt.ItemIsEditable) & ~Qt.ItemIsSelectable
            )
            self.detail_ingredients.setItem(i, 1, quantite_item)

            # Ajouter l'ID à la liste
            self.aliment_ids.append(aliment["id"])

            # Calories
            calories = aliment["calories"] * aliment["quantite"] / 100
            calories_item = QTableWidgetItem(f"{calories:.0f} kcal")
            calories_item.setTextAlignment(Qt.AlignCenter)  # Centrer le texte
            calories_item.setFlags(calories_item.flags() & ~Qt.ItemIsSelectable)
            self.detail_ingredients.setItem(i, 2, calories_item)

            # Macros
            macros = f"P: {aliment['proteines'] * aliment['quantite'] / 100:.1f}g | "
            macros += f"G: {aliment['glucides'] * aliment['quantite'] / 100:.1f}g | "
            macros += f"L: {aliment['lipides'] * aliment['quantite'] / 100:.1f}g"
            macros_item = QTableWidgetItem(macros)
            macros_item.setTextAlignment(Qt.AlignCenter)  # Centrer le texte
            macros_item.setFlags(macros_item.flags() & ~Qt.ItemIsSelectable)
            self.detail_ingredients.setItem(i, 3, macros_item)

            # Bouton de suppression (croix rouge) - version améliorée
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)  # Réduire les marges
            btn_layout.setSpacing(0)
            btn_layout.setAlignment(Qt.AlignCenter)  # Centrer dans la cellule

            btn_delete = QPushButton("〤")
            btn_delete.setObjectName("deleteButton")
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

        # Mettre à jour les valeurs nutritionnelles avec mise en forme
        self.calories_label.setText(f"{recette['total_calories']:.0f} kcal")
        self.proteines_label.setText(f"{recette['total_proteines']:.1f}g")
        self.glucides_label.setText(f"{recette['total_glucides']:.1f}g")
        self.lipides_label.setText(f"{recette['total_lipides']:.1f}g")

        # Ajouter des couleurs selon les valeurs
        self.calories_label.setStyleSheet(
            f"color: {'#e74c3c' if recette['total_calories'] > 500 else '#2ecc71'};"
        )
        self.proteines_label.setStyleSheet("color: #3498db;")
        self.glucides_label.setStyleSheet(
            f"color: {'#e67e22' if recette['total_glucides'] > 50 else '#2ecc71'};"
        )
        self.lipides_label.setStyleSheet(
            f"color: {'#e74c3c' if recette['total_lipides'] > 20 else '#2ecc71'};"
        )

    def ajouter_recette(self):
        """Ajoute une nouvelle recette"""
        dialog = RecetteDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # Ajouter la recette
            recette_id = self.db_manager.ajouter_repas_type(
                data["nom"], data["description"]
            )

            # Définir la catégorie et les portions
            if data["categorie_id"]:
                self.db_manager.set_categorie_repas_type(
                    recette_id, data["categorie_id"]
                )

            self.db_manager.set_portions_repas_type(
                recette_id,
                data["nb_portions"],
                data["temps_preparation"],
                data["temps_cuisson"],
            )

            # Rafraîchir l'affichage
            self.apply_filters()

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

        # Notifier que la recette a été modifiée
        EVENT_BUS.recette_modifiee.emit(recette_id)

    def create_nutrition_widget(self, title, value_label):
        """Crée un widget pour l'affichage d'une valeur nutritionnelle"""
        container = QFrame()
        container.setProperty("class", "nutrition-item")
        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 12, 8, 12)

        # Titre avec icône (emoji) et texte
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)

        # Choisir l'icône (emoji) selon le type de macro
        icon = ""
        if title == "Calories":
            icon = "🔥"  # Feu pour calories
        elif title == "Protéines":
            icon = "💪"  # Muscle pour protéines
        elif title == "Glucides":
            icon = "🌾"  # Blé pour glucides
        elif title == "Lipides":
            icon = "💧"  # Goutte pour lipides

        icon_label = QLabel(icon)
        icon_label.setProperty("class", "nutrition-icon")
        title_label = QLabel(title)
        title_label.setProperty("class", "nutrition-title")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)

        # Valeur nutritionnelle (grande et en gras)
        value_label.setAlignment(Qt.AlignCenter)

        # Ajouter au layout
        layout.addLayout(title_layout)
        layout.addWidget(value_label)

        return container

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
            self.db_manager.supprimer_aliment_repas_type(
                self.current_recette_id, aliment_id
            )

            # Rafraîchir l'affichage
            current_row = self.recettes_list.currentRow()
            self.afficher_details_recette(current_row)

            # Notifier que la recette a été modifiée
            EVENT_BUS.recette_modifiee.emit(self.current_recette_id)

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

        EVENT_BUS.recette_modifiee.emit(self.current_recette_id)

        # Afficher un message de confirmation
        QMessageBox.information(
            self, "Quantité mise à jour", "La quantité a été modifiée avec succès."
        )

    def modifier_recette(self):
        """Modifie la recette sélectionnée"""
        current_row = self.recettes_list.currentRow()
        if current_row < 0:
            return

        recette_id = self.recettes_list.item(current_row).data(Qt.UserRole)
        recette = self.db_manager.get_repas_type(recette_id)

        dialog = RecetteDialog(self, recette)
        if dialog.exec():
            data = dialog.get_data()

            # Mettre à jour la recette
            self.db_manager.modifier_repas_type(
                recette_id, data["nom"], data["description"]
            )

            # Mettre à jour la catégorie et les portions
            self.db_manager.set_categorie_repas_type(recette_id, data["categorie_id"])
            self.db_manager.set_portions_repas_type(
                recette_id,
                data["nb_portions"],
                data["temps_preparation"],
                data["temps_cuisson"],
            )

            # Rafraîchir l'affichage
            self.apply_filters()

            EVENT_BUS.recette_modifiee.emit(recette_id)

    def on_aliment_supprime(self):
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

        # Catégorie
        self.categorie_combo = QComboBox()
        self.categorie_combo.addItem("Sans catégorie", None)
        self.load_categories()
        layout.addRow("Catégorie:", self.categorie_combo)

        # Nombre de portions
        self.portions_spin = QSpinBox()
        self.portions_spin.setMinimum(1)
        self.portions_spin.setMaximum(20)
        self.portions_spin.setValue(
            self.recette["nb_portions"]
            if self.recette and "nb_portions" in self.recette
            else 1
        )
        layout.addRow("Nombre de portions:", self.portions_spin)

        # Temps de préparation
        self.prep_time_spin = QSpinBox()
        self.prep_time_spin.setMinimum(0)
        self.prep_time_spin.setMaximum(240)
        self.prep_time_spin.setSuffix(" min")
        self.prep_time_spin.setValue(
            self.recette["temps_preparation"]
            if self.recette and "temps_preparation" in self.recette
            else 0
        )
        layout.addRow("Temps de préparation:", self.prep_time_spin)

        # Temps de cuisson
        self.cooking_time_spin = QSpinBox()
        self.cooking_time_spin.setMinimum(0)
        self.cooking_time_spin.setMaximum(240)
        self.cooking_time_spin.setSuffix(" min")
        self.cooking_time_spin.setValue(
            self.recette["temps_cuisson"]
            if self.recette and "temps_cuisson" in self.recette
            else 0
        )
        layout.addRow("Temps de cuisson:", self.cooking_time_spin)

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

    def load_categories(self):
        """Charge les catégories dans le combobox"""
        parent = self.parent()
        db_manager = getattr(parent, "db_manager", None)

        if not db_manager:
            return

        categories = db_manager.get_categories()

        for categorie in categories:
            self.categorie_combo.addItem(categorie["nom"], categorie["id"])

        # Sélectionner la catégorie actuelle si modification
        if (
            self.recette
            and "categorie_id" in self.recette
            and self.recette["categorie_id"]
        ):
            index = self.categorie_combo.findData(self.recette["categorie_id"])
            if index >= 0:
                self.categorie_combo.setCurrentIndex(index)

    def get_data(self):
        """Récupère les données saisies"""
        return {
            "nom": self.nom_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "categorie_id": self.categorie_combo.currentData(),
            "nb_portions": self.portions_spin.value(),
            "temps_preparation": self.prep_time_spin.value(),
            "temps_cuisson": self.cooking_time_spin.value(),
        }


class IngredientRecetteDialog(QDialog):
    """Dialogue pour ajouter un ingrédient à une recette"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.aliment_ids = []
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
