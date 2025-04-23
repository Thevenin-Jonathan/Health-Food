from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QDoubleSpinBox,
    QMessageBox,
    QTabWidget,
    QWidget,
    QGridLayout,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from src.ui.dialogs.aliment_simple_selection_dialog import AlimentSimpleSelectionDialog


# Classe pour les items du tableau avec tri numérique correct
class NumericTableItem(QTableWidgetItem):
    def __init__(self, value, text=""):
        super().__init__(text)
        self.setData(Qt.UserRole, float(value) if value is not None else 0.0)
        self.setTextAlignment(Qt.AlignCenter)

    def __lt__(self, other):
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)


class AlimentComposeDialog(QDialog):
    """Dialogue pour créer ou modifier un aliment composé"""

    aliment_ajoute = Signal(int)  # Signal émis lorsqu'un nouvel aliment est ajouté
    aliment_modifie = Signal(int)  # Signal émis lorsqu'un aliment est modifié

    def __init__(self, parent=None, db_manager=None, aliment_compose=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.aliment_compose = aliment_compose
        self.ingredients = []
        self.mode_edition = aliment_compose is not None

        # Initialiser les attributs UI
        self.nom_input = None
        self.description_input = None
        self.categorie_combo = None
        self.ingredients_table = None

        # Valeurs nutritionnelles calculées
        self.calories_label = None
        self.proteines_label = None
        self.glucides_label = None
        self.lipides_label = None
        self.fibres_label = None
        self.cout_label = None

        self.setup_ui()

        # Si en mode édition, charger les données
        if self.mode_edition:
            self.charger_donnees()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle(
            "Aliment composé" if self.mode_edition else "Nouvel aliment composé"
        )
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)

        main_layout = QVBoxLayout(self)

        # Utiliser des onglets pour séparer les informations générales et la composition
        tab_widget = QTabWidget()

        # Onglet Informations générales
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)

        # Nom de l'aliment composé
        self.nom_input = QLineEdit()
        form_layout.addRow("Nom:", self.nom_input)

        # Description
        self.description_input = QLineEdit()
        form_layout.addRow("Description:", self.description_input)

        # Catégorie (avec auto-complétion)
        self.categorie_combo = QComboBox()
        self.categorie_combo.setEditable(True)
        self.charger_categories()
        form_layout.addRow("Catégorie:", self.categorie_combo)

        info_layout.addLayout(form_layout)

        # Résumé nutritionnel avec un style plus moderne
        nutrition_frame = QFrame()
        nutrition_frame.setObjectName("nutrition-frame")  # Pour cibler avec QSS
        nutrition_frame.setProperty("class", "nutrition-summary")  # Style existant
        nutrition_frame.setFrameShape(QFrame.StyledPanel)
        nutrition_frame.setMaximumWidth(300)  # Limite la largeur totale du cadre

        nutrition_layout = QGridLayout(nutrition_frame)
        nutrition_layout.setContentsMargins(15, 15, 15, 15)
        nutrition_layout.setVerticalSpacing(8)
        nutrition_layout.setHorizontalSpacing(15)

        # Titre de la section avec style amélioré
        title_label = QLabel("Valeurs nutritionnelles (pour 100g)")
        title_label.setProperty("class", "nutrition-title")
        title_label.setAlignment(Qt.AlignCenter)
        nutrition_layout.addWidget(title_label, 0, 0, 1, 3)

        # Ligne de séparation sous le titre avec container pour limiter sa largeur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #d1e3fa; margin: 5px 0px;")
        separator.setMaximumHeight(2)
        nutrition_layout.addWidget(separator, 1, 0, 1, 3)

        # Forcer les tailles de colonnes avec des widgets invisibles
        # Ces widgets agissent comme des "espaceurs" avec des tailles fixes
        spacer_icon = QWidget()
        spacer_icon.setFixedSize(30, 0)
        nutrition_layout.addWidget(spacer_icon, 2, 0)

        spacer_label = QWidget()
        spacer_label.setFixedSize(100, 0)  # Largeur du texte (ex: "Calories:")
        nutrition_layout.addWidget(spacer_label, 2, 1)

        spacer_value = QWidget()
        spacer_value.setFixedSize(80, 0)  # Largeur des valeurs (ex: "200 kcal")
        nutrition_layout.addWidget(spacer_value, 2, 2)

        # Ensuite, les données nutritionnelles
        nutrition_data = [
            ("🔥", "Calories:", "calories", "kcal", False),
            ("🥩", "Protéines:", "proteines", "g", True),
            ("🍞", "Glucides:", "glucides", "g", True),
            ("🥑", "Lipides:", "lipides", "g", True),
            ("🥦", "Fibres:", "fibres", "g", True),
            ("💰", "Coût:", "cout", "€", True),
        ]

        # Créer un widget conteneur avec taille fixe pour chaque ligne
        for row, (icon_text, label_text, attr_name, unit, decimal) in enumerate(
            nutrition_data, 3
        ):
            # Container pour cette ligne avec une taille maximale
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
            name_label.setFixedWidth(100)
            row_layout.addWidget(name_label)

            # Valeur
            value_label = QLabel(f"0{' '+unit}" if decimal else f"0 {unit}")
            value_label.setProperty("class", "nutrition-value")
            if attr_name != "cout":  # Ne pas appliquer de couleur au coût
                value_label.setProperty("type", attr_name)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setFixedWidth(80)
            row_layout.addWidget(value_label)

            # Stocker la référence pour mise à jour ultérieure
            setattr(self, f"{attr_name}_label", value_label)

            # Ajouter la ligne complète au layout principal
            nutrition_layout.addWidget(row_widget, row, 0, 1, 3)

        # Centrer le cadre nutritionnel dans son conteneur
        nutrition_container = QHBoxLayout()
        nutrition_container.addStretch()
        nutrition_container.addWidget(nutrition_frame)
        nutrition_container.addStretch()

        info_layout.addLayout(nutrition_container)
        info_layout.addStretch()

        tab_widget.addTab(info_widget, "Informations")

        # Onglet Ingrédients
        ingredients_widget = QWidget()
        ingredients_layout = QVBoxLayout(ingredients_widget)

        # Tableau des ingrédients - Suppression de la colonne ID
        self.ingredients_table = QTableWidget()
        self.ingredients_table.setSortingEnabled(True)  # Activer le tri
        self.ingredients_table.setColumnCount(6)
        self.ingredients_table.setHorizontalHeaderLabels(
            [
                "Nom",
                "Quantité (g)",
                "Calories",
                "Protéines (g)",
                "Glucides (g)",
                "Lipides (g)",
            ]
        )
        # Configuration des sections du header
        header = self.ingredients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nom
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.ingredients_table.setSelectionBehavior(QTableWidget.SelectRows)

        ingredients_layout.addWidget(self.ingredients_table)

        # Boutons pour gérer les ingrédients
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Ajouter un ingrédient")
        btn_add.clicked.connect(self.ajouter_ingredient)
        btn_remove = QPushButton("Supprimer")
        btn_remove.clicked.connect(self.supprimer_ingredient)

        # Ajouter le bouton pour éditer la quantité
        btn_edit = QPushButton("Modifier quantité")
        btn_edit.clicked.connect(self.modifier_quantite_ingredient)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_remove)

        ingredients_layout.addLayout(btn_layout)

        tab_widget.addTab(ingredients_widget, "Ingrédients")

        # Ajouter le widget d'onglets au layout principal
        main_layout.addWidget(tab_widget)

        # Boutons de validation/annulation
        buttons_layout = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Enregistrer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.validate_and_save)

        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_save)

        main_layout.addLayout(buttons_layout)

    def charger_categories(self):
        """Charge les catégories existantes dans le combobox"""
        categories = self.db_manager.get_categories_aliments_composes()
        self.categorie_combo.clear()
        self.categorie_combo.addItem("", "")  # Option vide
        for categorie in categories:
            self.categorie_combo.addItem(categorie, categorie)

    def charger_donnees(self):
        """Charge les données de l'aliment composé en mode édition"""
        if not self.aliment_compose:
            return

        # Informations de base
        self.nom_input.setText(self.aliment_compose["nom"])
        self.description_input.setText(self.aliment_compose.get("description", ""))

        # Catégorie
        if "categorie" in self.aliment_compose and self.aliment_compose["categorie"]:
            index = self.categorie_combo.findData(self.aliment_compose["categorie"])
            if index >= 0:
                self.categorie_combo.setCurrentIndex(index)
            else:
                self.categorie_combo.addItem(
                    self.aliment_compose["categorie"], self.aliment_compose["categorie"]
                )
                self.categorie_combo.setCurrentIndex(self.categorie_combo.count() - 1)

        # Ingrédients
        self.ingredients = self.aliment_compose.get("ingredients", [])
        self.actualiser_tableau_ingredients()

        # Mise à jour des valeurs nutritionnelles
        self.actualiser_valeurs_nutritionnelles()

    def actualiser_tableau_ingredients(self):
        """Met à jour le tableau des ingrédients"""
        # Mémoriser l'état de tri actuel
        sort_column = self.ingredients_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.ingredients_table.horizontalHeader().sortIndicatorOrder()

        # Désactiver le tri pendant la mise à jour
        self.ingredients_table.setSortingEnabled(False)

        # Vider le tableau
        self.ingredients_table.setRowCount(0)

        for i, ingredient in enumerate(self.ingredients):
            self.ingredients_table.insertRow(i)

            # Nom
            nom_item = QTableWidgetItem(ingredient["nom"])
            # Stocker l'ID comme donnée utilisateur
            nom_item.setData(Qt.UserRole + 1, ingredient["aliment_id"])
            self.ingredients_table.setItem(i, 0, nom_item)

            # Quantité
            quantite_item = NumericTableItem(
                ingredient["quantite"], f"{ingredient['quantite']:.0f}"
            )
            self.ingredients_table.setItem(i, 1, quantite_item)

            # Valeurs nutritionnelles pour la quantité indiquée
            ratio = ingredient["quantite"] / 100.0

            # Calories
            calories = ingredient["calories"] * ratio
            calories_item = NumericTableItem(calories, f"{calories:.0f}")
            self.ingredients_table.setItem(i, 2, calories_item)

            # Protéines
            proteines = ingredient["proteines"] * ratio
            proteines_item = NumericTableItem(proteines, f"{proteines:.1f}")
            self.ingredients_table.setItem(i, 3, proteines_item)

            # Glucides
            glucides = ingredient["glucides"] * ratio
            glucides_item = NumericTableItem(glucides, f"{glucides:.1f}")
            self.ingredients_table.setItem(i, 4, glucides_item)

            # Lipides
            lipides = ingredient["lipides"] * ratio
            lipides_item = NumericTableItem(lipides, f"{lipides:.1f}")
            self.ingredients_table.setItem(i, 5, lipides_item)

        # Réactiver le tri et restaurer l'état précédent
        self.ingredients_table.setSortingEnabled(True)
        if sort_column < self.ingredients_table.columnCount():
            self.ingredients_table.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )

    def actualiser_valeurs_nutritionnelles(self):
        """Calcule et affiche les valeurs nutritionnelles totales"""
        total_calories = 0
        total_proteines = 0
        total_glucides = 0
        total_lipides = 0
        total_fibres = 0
        total_cout = 0
        poids_total = 0

        for ingredient in self.ingredients:
            # Ajouter le poids de l'ingrédient au poids total
            poids_total += ingredient["quantite"]

            # Calculer les valeurs pour la quantité spécifiée
            ratio = ingredient["quantite"] / 100.0
            total_calories += ingredient["calories"] * ratio
            total_proteines += ingredient["proteines"] * ratio
            total_glucides += ingredient["glucides"] * ratio
            total_lipides += ingredient["lipides"] * ratio

            if "fibres" in ingredient and ingredient["fibres"]:
                total_fibres += ingredient["fibres"] * ratio

            if "prix_kg" in ingredient and ingredient["prix_kg"]:
                total_cout += (ingredient["prix_kg"] / 1000) * ingredient["quantite"]

        # Si le poids total est 0, éviter la division par zéro
        if poids_total == 0:
            self.calories_label.setText("0 kcal")
            self.proteines_label.setText("0 g")
            self.glucides_label.setText("0 g")
            self.lipides_label.setText("0 g")
            self.fibres_label.setText("0 g")
            self.cout_label.setText("0.00 €")
            return

        # Normaliser les valeurs pour 100g
        facteur_normalisation = 100.0 / poids_total
        calories_100g = total_calories * facteur_normalisation
        proteines_100g = total_proteines * facteur_normalisation
        glucides_100g = total_glucides * facteur_normalisation
        lipides_100g = total_lipides * facteur_normalisation
        fibres_100g = total_fibres * facteur_normalisation

        # Le coût est déjà pour la quantité totale, mais on peut le normaliser aussi si nécessaire
        cout_100g = total_cout * facteur_normalisation

        # Mettre à jour les étiquettes avec les valeurs normalisées
        self.calories_label.setText(f"{calories_100g:.0f} kcal")
        self.proteines_label.setText(f"{proteines_100g:.1f} g")
        self.glucides_label.setText(f"{glucides_100g:.1f} g")
        self.lipides_label.setText(f"{lipides_100g:.1f} g")
        self.fibres_label.setText(f"{fibres_100g:.1f} g")
        self.cout_label.setText(f"{cout_100g:.2f} €")

    def ajouter_ingredient(self):
        """Ouvre un dialogue pour ajouter un ingrédient"""

        # Calculer les valeurs nutritionnelles actuelles
        current_values = {
            "calories": sum(
                ingr["calories"] * ingr["quantite"] / 100 for ingr in self.ingredients
            ),
            "proteines": sum(
                ingr["proteines"] * ingr["quantite"] / 100 for ingr in self.ingredients
            ),
            "glucides": sum(
                ingr["glucides"] * ingr["quantite"] / 100 for ingr in self.ingredients
            ),
            "lipides": sum(
                ingr["lipides"] * ingr["quantite"] / 100 for ingr in self.ingredients
            ),
            "fibres": sum(
                ingr.get("fibres", 0) * ingr["quantite"] / 100
                for ingr in self.ingredients
            ),
        }

        dialog = AlimentSimpleSelectionDialog(self, self.db_manager, current_values)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()

            # Vérifier que l'aliment n'est pas déjà dans la liste
            for ingredient in self.ingredients:
                if ingredient["aliment_id"] == aliment_id:
                    QMessageBox.warning(
                        self,
                        "Ingrédient déjà présent",
                        "Cet ingrédient est déjà dans la liste. Veuillez modifier sa quantité si nécessaire.",
                    )
                    return

            # Récupérer les données de l'aliment
            aliment = self.db_manager.get_aliment(aliment_id)
            if aliment:
                # Créer un nouvel ingrédient
                nouvel_ingredient = {
                    "aliment_id": aliment_id,
                    "nom": aliment["nom"],
                    "quantite": quantite,
                    "calories": aliment["calories"],
                    "proteines": aliment["proteines"],
                    "glucides": aliment["glucides"],
                    "lipides": aliment["lipides"],
                    "fibres": aliment.get("fibres", 0),
                    "prix_kg": aliment.get("prix_kg", 0),
                }

                # Ajouter à la liste
                self.ingredients.append(nouvel_ingredient)

                # Mettre à jour l'interface
                self.actualiser_tableau_ingredients()
                self.actualiser_valeurs_nutritionnelles()

    def supprimer_ingredient(self):
        """Supprime l'ingrédient sélectionné"""
        selected_rows = self.ingredients_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Aucune sélection",
                "Veuillez sélectionner un ingrédient à supprimer.",
            )
            return

        # Obtenir l'index de la ligne sélectionnée
        row = selected_rows[0].row()

        # Récupérer l'ID de l'aliment et le nom depuis l'item
        aliment_id = self.ingredients_table.item(row, 0).data(Qt.UserRole + 1)
        nom_ingredient = self.ingredients_table.item(row, 0).text()

        # Trouver l'index correspondant dans la liste des ingrédients
        index_to_remove = None
        for i, ingredient in enumerate(self.ingredients):
            if ingredient["aliment_id"] == aliment_id:
                index_to_remove = i
                break

        if index_to_remove is None:
            QMessageBox.warning(
                self, "Erreur", "Impossible de trouver l'ingrédient dans la liste."
            )
            return

        # Demander confirmation
        confirmation = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'ingrédient {nom_ingredient} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation == QMessageBox.Yes:
            # Supprimer de la liste
            self.ingredients.pop(index_to_remove)

            # Mettre à jour l'interface
            self.actualiser_tableau_ingredients()
            self.actualiser_valeurs_nutritionnelles()

    def modifier_quantite_ingredient(self):
        """Modifie la quantité d'un ingrédient sélectionné"""
        selected_rows = self.ingredients_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Aucune sélection",
                "Veuillez sélectionner un ingrédient à modifier.",
            )
            return

        # Obtenir l'index de la ligne sélectionnée
        row = selected_rows[0].row()

        # Récupérer l'ingrédient actuel
        ingredient = self.ingredients[row]
        quantite_actuelle = ingredient["quantite"]

        # Créer le dialogue de quantité
        quantite_dialog = QDialog(self)
        quantite_dialog.setWindowTitle("Modifier la quantité")

        dialog_layout = QVBoxLayout(quantite_dialog)

        # Ajouter un label d'information
        info_label = QLabel(f"Quantité actuelle pour {ingredient['nom']} :")
        dialog_layout.addWidget(info_label)

        # Ajouter le spinbox pour la quantité
        quantite_spin = QDoubleSpinBox()
        quantite_spin.setRange(1, 5000)
        quantite_spin.setValue(quantite_actuelle)
        quantite_spin.setSuffix(" g")
        quantite_spin.setDecimals(0)
        dialog_layout.addWidget(quantite_spin)

        # Ajouter les boutons OK/Cancel
        buttons = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(quantite_dialog.accept)
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(quantite_dialog.reject)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_ok)
        dialog_layout.addLayout(buttons)

        # Exécuter le dialogue
        if quantite_dialog.exec():
            # Mettre à jour la quantité
            nouvelle_quantite = quantite_spin.value()
            self.ingredients[row]["quantite"] = nouvelle_quantite

            # Mettre à jour l'interface
            self.actualiser_tableau_ingredients()
            self.actualiser_valeurs_nutritionnelles()

    def validate_and_save(self):
        """Valide les données et sauvegarde l'aliment composé"""
        # Vérifications de base
        nom = self.nom_input.text().strip()
        if not nom:
            QMessageBox.warning(
                self,
                "Données incomplètes",
                "Veuillez spécifier un nom pour l'aliment composé.",
            )
            return

        if not self.ingredients:
            QMessageBox.warning(
                self,
                "Aucun ingrédient",
                "Veuillez ajouter au moins un ingrédient à l'aliment composé.",
            )
            return

        # Récupération des autres valeurs
        description = self.description_input.text().strip()
        categorie = self.categorie_combo.currentText().strip()

        try:
            if self.mode_edition:
                # Mode édition
                aliment_compose_id = self.aliment_compose["id"]

                # Mettre à jour les informations de base
                success = self.db_manager.modifier_aliment_compose(
                    aliment_compose_id, nom, description, categorie
                )
                if not success:
                    raise Exception(
                        "Erreur lors de la modification des informations de base"
                    )

                # Supprimer tous les ingrédients existants
                # (normalement ils sont supprimés automatiquement avec ON DELETE CASCADE)
                for ingredient in self.aliment_compose["ingredients"]:
                    self.db_manager.supprimer_ingredient_aliment_compose(
                        aliment_compose_id, ingredient["aliment_id"]
                    )

                # Ajouter les nouveaux ingrédients
                for ingredient in self.ingredients:
                    success = self.db_manager.ajouter_ingredient_aliment_compose(
                        aliment_compose_id,
                        ingredient["aliment_id"],
                        ingredient["quantite"],
                    )
                    if not success:
                        raise Exception(
                            f"Erreur lors de l'ajout de l'ingrédient {ingredient['nom']}"
                        )

                self.aliment_modifie.emit(aliment_compose_id)
                QMessageBox.information(
                    self, "Succès", "L'aliment composé a été modifié avec succès."
                )
            else:
                # Mode création
                aliment_compose_id = self.db_manager.ajouter_aliment_compose(
                    nom, description, categorie
                )
                if not aliment_compose_id:
                    raise Exception("Erreur lors de la création de l'aliment composé")

                # Ajouter les ingrédients
                for ingredient in self.ingredients:
                    success = self.db_manager.ajouter_ingredient_aliment_compose(
                        aliment_compose_id,
                        ingredient["aliment_id"],
                        ingredient["quantite"],
                    )
                    if not success:
                        raise Exception(
                            f"Erreur lors de l'ajout de l'ingrédient {ingredient['nom']}"
                        )

                self.aliment_ajoute.emit(aliment_compose_id)
                QMessageBox.information(
                    self, "Succès", "L'aliment composé a été créé avec succès."
                )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue lors de l'enregistrement: {str(e)}",
            )


class AlimentComposeSelectionDialog(QDialog):
    """Dialogue pour sélectionner un aliment composé et une quantité"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.aliment_compose_id = None
        self.quantite = 0

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Ajouter un aliment composé")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)

        # Sélection de la catégorie pour filtrer
        self.categorie_combo = QComboBox()
        self.categorie_combo.addItem("Toutes les catégories", "")
        categories = self.db_manager.get_categories_aliments_composes()
        for categorie in categories:
            self.categorie_combo.addItem(categorie, categorie)
        self.categorie_combo.currentIndexChanged.connect(self.filtrer_aliments)
        form_layout.addRow("Catégorie:", self.categorie_combo)

        # Sélection de l'aliment composé
        self.aliments_combo = QComboBox()
        self.charger_aliments_composes()
        self.aliments_combo.currentIndexChanged.connect(self.afficher_details_aliment)
        form_layout.addRow("Aliment composé:", self.aliments_combo)

        # Quantité
        self.quantite_spin = QDoubleSpinBox()
        self.quantite_spin.setMinimum(1)
        self.quantite_spin.setMaximum(1000)
        self.quantite_spin.setValue(100)
        self.quantite_spin.setSuffix(" g")
        form_layout.addRow("Quantité:", self.quantite_spin)

        layout.addLayout(form_layout)

        # Informations sur l'aliment avec un style plus moderne
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)

        info_layout = QVBoxLayout(info_frame)

        self.info_label = QLabel()
        self.info_label.setTextFormat(Qt.RichText)
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_frame)

        # Connecter le changement de quantité pour mise à jour en temps réel
        self.quantite_spin.valueChanged.connect(self.afficher_details_aliment)

        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)

        add_btn = QPushButton("Ajouter")
        add_btn.setDefault(True)
        add_btn.clicked.connect(self.accept)

        # Bouton pour gérer les aliments composés
        manage_btn = QPushButton("Gérer les aliments composés")
        manage_btn.clicked.connect(self.gerer_aliments_composes)

        buttons_layout.addWidget(manage_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)

        layout.addLayout(buttons_layout)

        # Afficher les détails du premier aliment
        self.afficher_details_aliment()

    def charger_aliments_composes(self, categorie=None):
        """Charge la liste des aliments composés"""
        self.aliments_combo.clear()

        aliments_composes = self.db_manager.get_aliments_composes(categorie)

        if not aliments_composes:
            self.aliments_combo.addItem("Aucun aliment composé disponible", None)
            return

        for aliment in aliments_composes:
            self.aliments_combo.addItem(aliment["nom"], aliment["id"])

    def filtrer_aliments(self):
        """Filtre les aliments selon la catégorie sélectionnée"""
        categorie = self.categorie_combo.currentData()
        self.charger_aliments_composes(categorie)

    def afficher_details_aliment(self):
        """Affiche les détails de l'aliment composé sélectionné avec quantité mise à jour"""
        aliment_id = self.aliments_combo.currentData()

        if not aliment_id:
            self.info_label.setText("")
            return

        aliment = self.db_manager.get_aliment_compose(aliment_id)
        if not aliment:
            self.info_label.setText("<i>Aucune information disponible</i>")
            return

        # Récupérer la quantité actuelle
        quantite = self.quantite_spin.value()
        ratio = quantite / 100.0

        # Calculer les valeurs nutritionnelles pour la quantité actuelle
        calories = aliment["total_calories"] * ratio
        proteines = aliment["total_proteines"] * ratio
        glucides = aliment["total_glucides"] * ratio
        lipides = aliment["total_lipides"] * ratio

        html = f"""
        <h3 style="margin-top:0;">{aliment['nom']}</h3>
        <p style="color:#555;">{aliment.get('description', '')}</p>
        <p><b>Composition:</b></p>
        <ul style="margin-top:5px;">
        """

        # Afficher les ingrédients ajustés à la quantité sélectionnée
        for ingredient in aliment["ingredients"]:
            ing_quantite = ingredient["quantite"] * ratio
            html += f"<li>{ingredient['nom']}: {ing_quantite:.0f}g</li>"

        html += f"""
        </ul>
        <p><b>Valeurs nutritionnelles pour {quantite:.0f}g:</b></p>
        <table style="width:100%; margin-top:5px;">
            <tr><td>Calories:</td><td align="right"><b>{calories:.0f} kcal</b></td></tr>
            <tr><td>Protéines:</td><td align="right"><b>{proteines:.1f}g</b></td></tr>
            <tr><td>Glucides:</td><td align="right"><b>{glucides:.1f}g</b></td></tr>
            <tr><td>Lipides:</td><td align="right"><b>{lipides:.1f}g</b></td></tr>
        </table>
        """

        self.info_label.setText(html)

    # Ajout d'une fonction pour appliquer les statuts aux barres de progression
    def _set_progress_bar_color(self, progress_bar, percentage):
        """Définit la couleur de la barre de progression en fonction du pourcentage"""
        # Vérifier si percentage est valide
        if percentage == float("inf") or percentage != percentage:  # inf ou NaN
            percentage = 0  # Valeur par défaut sécuritaire

        # Définir le statut basé sur le pourcentage
        if percentage > 1.05:
            status = "over"  # Rouge - trop élevé
        elif 0.95 <= percentage <= 1.05:
            status = "good"  # Vert - idéal
        elif 0.5 <= percentage < 0.95:
            status = "medium"  # Orange - moyen
        else:
            status = "low"  # Gris - trop bas

        # Appliquer le statut comme propriété QSS
        progress_bar.setProperty("status", status)

        # Forcer la mise à jour du style
        progress_bar.style().unpolish(progress_bar)
        progress_bar.style().polish(progress_bar)

    def gerer_aliments_composes(self):
        """Ouvre le gestionnaire d'aliments composés"""
        dialog = AlimentsComposesManagerDialog(self, self.db_manager)
        if dialog.exec():
            # Recharger la liste
            self.charger_aliments_composes(self.categorie_combo.currentData())
            self.afficher_details_aliment()

    def get_data(self):
        """Retourne l'ID de l'aliment composé et la quantité sélectionnés"""
        return (self.aliments_combo.currentData(), self.quantite_spin.value())


class AlimentsComposesManagerDialog(QDialog):
    """Dialogue pour gérer (créer, modifier, supprimer) les aliments composés"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.charger_aliments_composes()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Gestionnaire d'aliments composés")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)

        # Filtres
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filtrer par catégorie:"))
        self.categorie_combo = QComboBox()
        self.categorie_combo.addItem("Toutes les catégories", "")
        categories = self.db_manager.get_categories_aliments_composes()
        for categorie in categories:
            self.categorie_combo.addItem(categorie, categorie)
        self.categorie_combo.currentIndexChanged.connect(self.filtrer_aliments)
        filter_layout.addWidget(self.categorie_combo)

        filter_layout.addStretch()

        # Boutons d'action
        self.btn_add = QPushButton("Ajouter")
        self.btn_add.clicked.connect(self.ajouter_aliment_compose)
        filter_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Modifier")
        self.btn_edit.clicked.connect(self.modifier_aliment_compose)
        filter_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.clicked.connect(self.supprimer_aliment_compose)
        filter_layout.addWidget(self.btn_delete)

        layout.addLayout(filter_layout)

        # Tableau des aliments composés - Suppression de la colonne ID
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)  # Activer le tri
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Nom", "Catégorie", "Calories", "Protéines", "Nb ingrédients"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )  # Nom
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )  # Catégorie
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )  # Calories
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )  # Protéines
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeToContents
        )  # Nb ingrédients

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemDoubleClicked.connect(self.modifier_aliment_compose)

        layout.addWidget(self.table)

        # Bouton de fermeture
        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def charger_aliments_composes(self, categorie=None):
        """Charge la liste des aliments composés dans le tableau"""
        # Mémoriser l'état de tri actuel
        header = self.table.horizontalHeader()
        sortColumn = header.sortIndicatorSection()
        sortOrder = header.sortIndicatorOrder()

        # Désactiver temporairement le tri
        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)

        aliments = self.db_manager.get_aliments_composes(categorie)
        self.table.setRowCount(len(aliments))

        for i, aliment in enumerate(aliments):
            # Nom avec ID stockée comme donnée utilisateur
            nom_item = QTableWidgetItem(aliment["nom"])
            nom_item.setData(Qt.UserRole + 1, aliment["id"])
            self.table.setItem(i, 0, nom_item)

            # Catégorie
            categorie_item = QTableWidgetItem(aliment.get("categorie", ""))
            self.table.setItem(i, 1, categorie_item)

            # Calories (avec tri numérique)
            calories_item = NumericTableItem(
                aliment["total_calories"], f"{aliment['total_calories']:.0f} kcal"
            )
            self.table.setItem(i, 2, calories_item)

            # Protéines (avec tri numérique)
            proteines_item = NumericTableItem(
                aliment["total_proteines"], f"{aliment['total_proteines']:.1f}g"
            )
            self.table.setItem(i, 3, proteines_item)

            # Nombre d'ingrédients (avec tri numérique)
            nb_ingredients = len(aliment["ingredients"])
            nb_ing_item = NumericTableItem(nb_ingredients, str(nb_ingredients))
            self.table.setItem(i, 4, nb_ing_item)

        # Réactiver le tri et restaurer l'état précédent
        self.table.setSortingEnabled(True)
        if sortColumn < self.table.columnCount():
            header.setSortIndicator(sortColumn, sortOrder)

    def filtrer_aliments(self):
        """Filtre la liste des aliments selon la catégorie sélectionnée"""
        categorie = self.categorie_combo.currentData()
        self.charger_aliments_composes(categorie)

    def ajouter_aliment_compose(self):
        """Ouvre le dialogue pour ajouter un nouvel aliment composé"""
        dialog = AlimentComposeDialog(self, self.db_manager)
        dialog.aliment_ajoute.connect(self.filtrer_aliments)
        dialog.exec()

    def modifier_aliment_compose(self):
        """Ouvre le dialogue pour modifier l'aliment composé sélectionné"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Aucune sélection",
                "Veuillez sélectionner un aliment composé à modifier.",
            )
            return

        # Obtenir l'ID de l'aliment depuis l'item
        row = selected_rows[0].row()
        aliment_id = self.table.item(row, 0).data(Qt.UserRole + 1)

        # Récupérer les données complètes
        aliment = self.db_manager.get_aliment_compose(aliment_id)
        if not aliment:
            QMessageBox.warning(
                self,
                "Erreur",
                "Impossible de récupérer les informations de l'aliment composé.",
            )
            return

        # Ouvrir le dialogue d'édition
        dialog = AlimentComposeDialog(self, self.db_manager, aliment)
        dialog.aliment_modifie.connect(self.filtrer_aliments)
        dialog.exec()

    def supprimer_aliment_compose(self):
        """Supprime l'aliment composé sélectionné"""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "Aucune sélection",
                "Veuillez sélectionner un aliment composé à supprimer.",
            )
            return

        # Obtenir l'ID et le nom de l'aliment
        row = selected_rows[0].row()
        aliment_id = self.table.item(row, 0).data(Qt.UserRole + 1)
        aliment_nom = self.table.item(row, 0).text()

        # Demander confirmation
        confirmation = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer l'aliment composé '{aliment_nom}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirmation == QMessageBox.Yes:
            # Supprimer l'aliment
            success = self.db_manager.supprimer_aliment_compose(aliment_id)

            if success:
                QMessageBox.information(
                    self, "Succès", f"L'aliment composé '{aliment_nom}' a été supprimé."
                )
                self.filtrer_aliments()  # Rafraîchir la liste
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de supprimer l'aliment composé '{aliment_nom}'.",
                )
