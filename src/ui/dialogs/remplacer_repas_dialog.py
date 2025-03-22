from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDoubleSpinBox,
    QSplitter,
    QFormLayout,
    QScrollArea,
    QWidget,
    QMessageBox,
    QListWidget,
    QGridLayout,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt

from src.ui.widgets.aliment_slider_widget import AlimentSliderWidget
from src.ui.widgets.nutrition_comparison import NutritionComparison


class AjouterIngredientDialog(QDialog):
    """Dialogue pour ajouter un ingrédient à la recette en prévisualisation"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.aliment_ids = []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un ingrédient")
        self.setMinimumWidth(400)

        layout = QFormLayout()

        # Sélection de l'aliment
        self.aliment_combo = QComboBox()
        self.load_aliments()
        layout.addRow("Aliment:", self.aliment_combo)

        # Quantité en grammes - amélioration du contrôle avec orientation verticale
        self.quantite_input = QDoubleSpinBox()
        self.quantite_input.setMinimum(1)
        self.quantite_input.setMaximum(5000)
        self.quantite_input.setValue(100)
        self.quantite_input.setSuffix(" g")
        # Configuration pour une meilleure utilisation des flèches
        self.quantite_input.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self.quantite_input.setSingleStep(10)  # Incrément de 10g par défaut
        self.quantite_input.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        self.quantite_input.setProperty("class", "spin-box-vertical")
        self.quantite_input.valueChanged.connect(self.update_info)
        layout.addRow("Quantité:", self.quantite_input)

        # Label pour afficher les macros proportionnellement au poids
        self.macros_label = QLabel("")
        self.macros_label.setWordWrap(True)
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

        # Appeler update_info pour afficher les informations de l'aliment par défaut
        if self.aliment_combo.count() > 0:
            self.update_info()

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

            # Information proportionnelle au poids
            ratio = quantite / 100.0
            macro_text = f"<b>Calories:</b> {aliment['calories'] * ratio:.0f} kcal<br>"
            macro_text += f"<b>Protéines:</b> {aliment['proteines'] * ratio:.1f}g<br>"
            macro_text += f"<b>Glucides:</b> {aliment['glucides'] * ratio:.1f}g<br>"
            macro_text += f"<b>Lipides:</b> {aliment['lipides'] * ratio:.1f}g"
            self.macros_label.setText(macro_text)

    def get_data(self):
        if self.aliment_combo.currentIndex() < 0:
            return None, 0

        aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
        return aliment_id, self.quantite_input.value()


class RemplacerRepasDialog(QDialog):
    """Dialogue pour remplacer un repas par une recette avec prévisualisation avancée"""

    def __init__(self, parent=None, db_manager=None, repas_actuel=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.repas_actuel = repas_actuel
        self.recette_courante_id = None
        self.facteurs_quantite = {}
        self.nouveaux_aliments = []  # Liste pour stocker les aliments ajoutés
        self.aliments_exclus = []  # Liste des IDs d'aliments à exclure
        self.recette_aliments = []  # Liste des aliments de la recette courante
        self.recette_modifiee = None  # Recette modifiée après ajustements
        self.sliders = (
            {}
        )  # Dictionnaire pour stocker les références aux sliders {aliment_id: slider}
        self.recette_courante = None  # La recette sélectionnée

        # Récupérer les totaux du jour si disponibles
        self.totaux_jour = None
        if repas_actuel and repas_actuel.get("jour"):
            for jour, repas_list in self.db_manager.get_repas_semaine(
                repas_actuel.get("semaine_id")
            ).items():
                if jour == repas_actuel["jour"]:
                    # Calculer les totaux du jour
                    cal_total = sum(r["total_calories"] for r in repas_list)
                    prot_total = sum(r["total_proteines"] for r in repas_list)
                    gluc_total = sum(r["total_glucides"] for r in repas_list)
                    lip_total = sum(r["total_lipides"] for r in repas_list)

                    self.totaux_jour = {
                        "calories": cal_total,
                        "proteines": prot_total,
                        "glucides": gluc_total,
                        "lipides": lip_total,
                    }
                    break

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Remplacer un repas")
        self.setMinimumSize(1200, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Grille pour l'en-tête (gain de place vertical)
        header_layout = QGridLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(10)

        # Titre et sélection de recette sur la même ligne
        title = QLabel("<h2>Remplacer un repas</h2>")
        header_layout.addWidget(title, 0, 0)

        # Sélection de recette
        recette_label = QLabel("Recette:")
        recette_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(recette_label, 0, 1)

        self.recette_combo = QComboBox()
        self.recette_combo.setMinimumWidth(300)
        self.charger_recettes()
        # Connecter le changement de recette directement à la prévisualisation
        self.recette_combo.currentIndexChanged.connect(self.previsualiser_recette)
        header_layout.addWidget(self.recette_combo, 0, 2)

        # Configurer l'étirement des colonnes
        header_layout.setColumnStretch(0, 3)
        header_layout.setColumnStretch(1, 0)
        header_layout.setColumnStretch(2, 2)

        main_layout.addLayout(header_layout)

        # Splitter principal pour la zone de contenu
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # PANNEAU GAUCHE: Repas actuel - Approche avec QLabel et QFrame
        repas_actuel_container = QWidget()
        repas_actuel_layout = QVBoxLayout(repas_actuel_container)
        repas_actuel_layout.setContentsMargins(5, 5, 5, 5)

        # Titre avec QLabel
        title_label = QLabel("<strong>Repas Actuel</strong>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("class", "group-title")
        title_label.setObjectName("repasActuelTitle")
        title_label.setMinimumHeight(25)  # Pour assurer un espacement suffisant
        repas_actuel_layout.addWidget(title_label)

        # Contenu du groupe
        content_frame = QFrame()
        content_frame.setProperty("class", "group-content")
        content_frame.setObjectName("repasActuelContent")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(2, 2, 2, 2)

        # Tableau des aliments actuels (configuration reste identique)
        self.repas_actuel_table = QTableWidget()
        self.repas_actuel_table.setObjectName("repasActuelTable")
        self.repas_actuel_table.setColumnCount(4)
        self.repas_actuel_table.setHorizontalHeaderLabels(
            ["ID", "Aliment", "Quantité", "Calories"]
        )

        # Configuration du tableau - le code reste inchangé
        self.repas_actuel_table.horizontalHeader().setMinimumHeight(30)
        self.repas_actuel_table.verticalHeader().setDefaultSectionSize(30)
        self.repas_actuel_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.repas_actuel_table.setColumnWidth(1, 200)
        self.repas_actuel_table.setColumnWidth(2, 70)
        self.repas_actuel_table.setColumnWidth(3, 70)
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Fixed
        )
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Fixed
        )
        self.repas_actuel_table.hideColumn(0)
        self.repas_actuel_table.setAlternatingRowColors(True)
        self.repas_actuel_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.repas_actuel_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.repas_actuel_table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.repas_actuel_table.verticalHeader().setVisible(False)

        # Ajouter le tableau au layout du frame
        content_layout.addWidget(self.repas_actuel_table)

        # Ajouter le frame au layout principal
        repas_actuel_layout.addWidget(content_frame)

        # Ajouter le conteneur au splitter
        main_splitter.addWidget(repas_actuel_container)

        # PANNEAU CENTRAL: Nouveau repas
        nouveau_repas_container = QWidget()
        nouveau_repas_layout = QVBoxLayout(nouveau_repas_container)
        nouveau_repas_layout.setContentsMargins(5, 5, 5, 5)

        # Titre avec QLabel
        nouveau_repas_title = QLabel("<strong>Nouveau repas</strong>")
        nouveau_repas_title.setAlignment(Qt.AlignCenter)
        nouveau_repas_title.setProperty("class", "group-title")
        nouveau_repas_title.setObjectName("nouveauRepasTitle")
        nouveau_repas_title.setMinimumHeight(25)
        nouveau_repas_layout.addWidget(nouveau_repas_title)

        # Contenu du groupe
        nouveau_repas_frame = QFrame()
        nouveau_repas_frame.setProperty("class", "group-content")
        nouveau_repas_frame.setObjectName("nouveauRepasContent")
        nouveau_repas_content_layout = QVBoxLayout(nouveau_repas_frame)
        nouveau_repas_content_layout.setContentsMargins(2, 2, 2, 2)

        # Zone de scroll pour les sliders d'aliments
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(15)
        scroll_area.setWidget(scroll_widget)

        nouveau_repas_content_layout.addWidget(scroll_area)

        # Boutons pour modifier la recette
        btn_layout = QHBoxLayout()

        self.btn_add_ingredient = QPushButton("+ Ajouter un aliment")
        self.btn_add_ingredient.clicked.connect(self.ajouter_ingredient)
        btn_layout.addWidget(self.btn_add_ingredient)

        self.btn_remove_ingredient = QPushButton("- Retirer un aliment")
        self.btn_remove_ingredient.clicked.connect(self.retirer_ingredient)
        btn_layout.addWidget(self.btn_remove_ingredient)

        nouveau_repas_content_layout.addLayout(btn_layout)

        nouveau_repas_layout.addWidget(nouveau_repas_frame)

        main_splitter.addWidget(nouveau_repas_container)

        # PANNEAU DROIT: Comparaison nutritionnelle
        self.nutrition_comparison = NutritionComparison(db_manager=self.db_manager)
        main_splitter.addWidget(self.nutrition_comparison)

        # Définir les proportions relatives des panneaux
        main_splitter.setSizes([300, 500, 400])
        main_layout.addWidget(main_splitter)

        # Boutons d'action en bas
        buttons_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = QPushButton("Appliquer les modifications")
        self.btn_apply.clicked.connect(self.accept)
        self.btn_apply.setEnabled(False)  # Désactivé jusqu'à la sélection d'une recette

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_apply)

        main_layout.addLayout(buttons_layout)

        # Remplir la table du repas actuel
        self.afficher_repas_actuel()

    def charger_recettes(self):
        """Charge les recettes disponibles dans le combo box"""
        self.recette_combo.clear()

        # Ajouter "Aucune recette" comme première option
        self.recette_combo.addItem("Aucune recette sélectionnée", None)

        # Charger les recettes depuis la base de données
        recettes = self.db_manager.get_repas_types()

        for recette in recettes:
            self.recette_combo.addItem(recette["nom"], recette["id"])

    def afficher_repas_actuel(self):
        """Affiche le repas actuel dans le tableau"""
        if not self.repas_actuel:
            return

        # Configurer le tableau
        self.repas_actuel_table.setRowCount(len(self.repas_actuel["aliments"]))

        # Remplir les données
        for i, aliment in enumerate(self.repas_actuel["aliments"]):
            # ID (caché)
            id_item = QTableWidgetItem(str(aliment["id"]))
            self.repas_actuel_table.setItem(i, 0, id_item)

            # Nom de l'aliment
            nom = f"{aliment['nom']}"
            if aliment.get("marque"):
                nom += f" ({aliment['marque']})"

            nom_item = QTableWidgetItem(nom)
            nom_item.setToolTip(nom)  # Ajouter un tooltip pour les noms longs
            self.repas_actuel_table.setItem(i, 1, nom_item)

            # Quantité
            quantite_item = QTableWidgetItem(f"{aliment['quantite']:.0f}g")
            quantite_item.setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )  # Alignement à droite
            self.repas_actuel_table.setItem(i, 2, quantite_item)

            # Calories
            calories = aliment["calories"] * aliment["quantite"] / 100
            calories_item = QTableWidgetItem(f"{calories:.0f} kcal")
            calories_item.setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )  # Alignement à droite
            self.repas_actuel_table.setItem(i, 3, calories_item)

    def previsualiser_recette(self):
        """Affiche la prévisualisation de la recette sélectionnée"""
        recette_id = self.recette_combo.currentData()
        if not recette_id:
            # Nettoyer l'interface si aucune recette n'est sélectionnée
            self._clear_scroll_layout()
            self.btn_apply.setEnabled(False)
            return

        # Mémoriser l'ID de la recette courante
        self.recette_courante_id = recette_id

        # Charger la recette
        self.recette_courante = self.db_manager.get_repas_type(recette_id)

        # Effacer les sliders existants
        self._clear_scroll_layout()

        # Initialiser les données des aliments et facteurs
        self.facteurs_quantite = {}
        self.nouveaux_aliments = []
        self.aliments_exclus = []
        self.sliders = {}  # Réinitialiser le dictionnaire de sliders

        # Créer un slider pour chaque aliment de la recette
        for aliment in self.recette_courante["aliments"]:
            self._ajouter_slider_aliment(aliment)

        # Calcul initial de la recette modifiée
        self._calculer_recette_modifiee()

        # Mettre à jour la comparaison nutritionnelle
        self.nutrition_comparison.update_comparison(
            self.repas_actuel, self.recette_modifiee, self.totaux_jour
        )

        # Activer le bouton d'application
        self.btn_apply.setEnabled(True)

    def _clear_scroll_layout(self):
        """Nettoie tous les widgets dans la zone de défilement"""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.sliders = {}  # Réinitialiser les références aux sliders

    def _ajouter_slider_aliment(self, aliment):
        """Ajoute un slider pour un aliment"""
        slider = AlimentSliderWidget(
            aliment["id"],
            f"{aliment['nom']} ({aliment.get('marque', '')})",
            aliment["quantite"],
        )
        slider.quantityChanged.connect(self.on_quantity_changed)
        self.scroll_layout.addWidget(slider)

        # Stocker une référence au slider
        self.sliders[aliment["id"]] = slider

        # Initialiser le facteur à 1.0 pour cet aliment
        self.facteurs_quantite[aliment["id"]] = 1.0

    def on_quantity_changed(self, aliment_id, nouvelle_quantite):
        """Appelé quand la quantité d'un aliment est modifiée via un slider"""
        # Trouver l'aliment et mettre à jour sa quantité directement

        # Vérifier dans la recette courante
        if self.recette_courante:
            for aliment in self.recette_courante["aliments"]:
                if aliment["id"] == aliment_id:
                    # Pour les aliments de la recette, calculer le facteur
                    facteur = nouvelle_quantite / aliment["quantite"]
                    self.facteurs_quantite[aliment_id] = facteur
                    self._calculer_recette_modifiee()
                    return

        # Vérifier dans les nouveaux aliments
        for i, aliment in enumerate(self.nouveaux_aliments):
            if aliment["id"] == aliment_id:
                # Pour les nouveaux aliments, mettre à jour directement la quantité
                self.nouveaux_aliments[i]["quantite"] = nouvelle_quantite
                # Calculer également le facteur (pour la cohérence)
                facteur = nouvelle_quantite / aliment["quantite_base"]
                self.facteurs_quantite[aliment_id] = facteur
                self._calculer_recette_modifiee()
                return

        # Recalculer la recette modifiée si l'aliment n'est pas trouvé
        self._calculer_recette_modifiee()

    def _calculer_recette_modifiee(self):
        """Calcule la recette modifiée en fonction des facteurs et modifications"""
        # Créer une copie modifiable de la recette ou initialiser un nouveau repas si aucune recette n'est sélectionnée
        self.recette_modifiee = {
            "id": self.recette_courante["id"] if self.recette_courante else None,
            "nom": (
                self.recette_courante["nom"]
                if self.recette_courante
                else "Recette personnalisée"
            ),
            "aliments": [],
            "total_calories": 0,
            "total_proteines": 0,
            "total_glucides": 0,
            "total_lipides": 0,
        }

        # Ajouter les aliments de la recette originale (sauf exclus)
        if self.recette_courante:
            for aliment in self.recette_courante["aliments"]:
                if aliment["id"] not in self.aliments_exclus:
                    # Obtenir le facteur correct pour cet aliment
                    facteur = self.facteurs_quantite.get(aliment["id"], 1.0)
                    nouvelle_quantite = aliment["quantite"] * facteur

                    # Créer une copie modifiée de l'aliment
                    aliment_modifie = aliment.copy()
                    aliment_modifie["quantite"] = nouvelle_quantite
                    aliment_modifie["quantite_base"] = aliment[
                        "quantite"
                    ]  # Conserver la quantité de base

                    # Calculer les valeurs nutritionnelles pour la nouvelle quantité
                    aliment_modifie["calories_totales"] = (
                        aliment["calories"] * nouvelle_quantite / 100
                    )
                    aliment_modifie["proteines_totales"] = (
                        aliment["proteines"] * nouvelle_quantite / 100
                    )
                    aliment_modifie["glucides_totales"] = (
                        aliment["glucides"] * nouvelle_quantite / 100
                    )
                    aliment_modifie["lipides_totales"] = (
                        aliment["lipides"] * nouvelle_quantite / 100
                    )

                    # Ajouter aux totaux
                    self.recette_modifiee["total_calories"] += aliment_modifie[
                        "calories_totales"
                    ]
                    self.recette_modifiee["total_proteines"] += aliment_modifie[
                        "proteines_totales"
                    ]
                    self.recette_modifiee["total_glucides"] += aliment_modifie[
                        "glucides_totales"
                    ]
                    self.recette_modifiee["total_lipides"] += aliment_modifie[
                        "lipides_totales"
                    ]

                    # Ajouter l'aliment à la liste
                    self.recette_modifiee["aliments"].append(aliment_modifie)

        # Ajouter les nouveaux aliments (sauf exclus)
        for nouvel_aliment in self.nouveaux_aliments:
            if nouvel_aliment["id"] not in self.aliments_exclus:
                # Calculer les valeurs nutritionnelles pour la quantité actuelle
                quantite = nouvel_aliment["quantite"]

                # Créer une copie modifiée avec les valeurs nutritionnelles calculées
                aliment_modifie = nouvel_aliment.copy()
                aliment_modifie["calories_totales"] = (
                    nouvel_aliment["calories"] * quantite / 100
                )
                aliment_modifie["proteines_totales"] = (
                    nouvel_aliment["proteines"] * quantite / 100
                )
                aliment_modifie["glucides_totales"] = (
                    nouvel_aliment["glucides"] * quantite / 100
                )
                aliment_modifie["lipides_totales"] = (
                    nouvel_aliment["lipides"] * quantite / 100
                )

                # Ajouter aux totaux
                self.recette_modifiee["total_calories"] += aliment_modifie[
                    "calories_totales"
                ]
                self.recette_modifiee["total_proteines"] += aliment_modifie[
                    "proteines_totales"
                ]
                self.recette_modifiee["total_glucides"] += aliment_modifie[
                    "glucides_totales"
                ]
                self.recette_modifiee["total_lipides"] += aliment_modifie[
                    "lipides_totales"
                ]

                # Ajouter l'aliment à la liste
                self.recette_modifiee["aliments"].append(aliment_modifie)

        # Mettre à jour la comparaison nutritionnelle
        self.nutrition_comparison.update_comparison(
            self.repas_actuel, self.recette_modifiee, self.totaux_jour
        )

    def ajouter_ingredient(self):
        """Ajoute un nouvel ingrédient à la recette"""
        if not self.recette_modifiee:
            QMessageBox.warning(
                self,
                "Aucune recette prévisualisée",
                "Veuillez d'abord prévisualiser une recette avant d'ajouter des aliments.",
            )
            return

        dialog = AjouterIngredientDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()

            # Vérifier si cet aliment n'est pas déjà dans la recette
            for aliment in self.recette_modifiee["aliments"]:
                if aliment["id"] == aliment_id:
                    # Si l'aliment existe déjà, mettre à jour son slider et sa quantité
                    if aliment_id in self.sliders:
                        # Augmenter la quantité actuelle
                        nouvelle_quantite = aliment["quantite"] + quantite

                        # Récupérer la quantité de base de la slider qui existe déjà
                        slider = self.sliders[aliment_id]

                        # Mettre à jour directement la valeur du spinbox
                        slider.spinbox.blockSignals(True)
                        slider.spinbox.setValue(int(nouvelle_quantite))
                        slider.spinbox.blockSignals(False)

                        # Mettre à jour la valeur du slider en fonction de la nouvelle quantité
                        quantite_base = slider.quantite_base
                        nouveau_facteur = nouvelle_quantite / quantite_base
                        slider.slider.blockSignals(True)
                        slider.slider.setValue(int(nouveau_facteur * 100))
                        slider.slider.blockSignals(False)

                        # Émettre le signal manuellement pour s'assurer que tout est mis à jour
                        self.on_quantity_changed(aliment_id, nouvelle_quantite)

                        QMessageBox.information(
                            self,
                            "Aliment déjà présent",
                            "Cet aliment est déjà présent. Sa quantité a été augmentée.",
                        )
                        return

            # Si on arrive ici, l'aliment n'existe pas encore dans la recette
            # Récupérer les données complètes de l'aliment
            aliment = self.db_manager.get_aliment(aliment_id)

            # Créer un objet aliment complet
            nouvel_aliment = {
                "id": aliment["id"],
                "nom": aliment["nom"],
                "marque": aliment["marque"],
                "quantite": quantite,  # Quantité courante
                "quantite_base": quantite,  # Quantité de référence pour les facteurs
                "calories": aliment["calories"],
                "proteines": aliment["proteines"],
                "glucides": aliment["glucides"],
                "lipides": aliment["lipides"],
                "fibres": aliment.get("fibres", 0),
                "prix_kg": aliment.get("prix_kg", 0),
            }

            # Ajouter à la liste des nouveaux aliments
            self.nouveaux_aliments.append(nouvel_aliment)

            # Créer un nouveau slider pour cet aliment
            slider = AlimentSliderWidget(
                aliment["id"],
                f"{aliment['nom']} ({aliment.get('marque', '')})",
                quantite,
            )

            # Connecter le signal APRÈS l'initialisation complète
            slider.quantityChanged.connect(self.on_quantity_changed)

            # Ajouter le slider à l'interface
            self.scroll_layout.addWidget(slider)

            # Stocker une référence au slider
            self.sliders[aliment["id"]] = slider

            # Mettre à jour la recette
            self._calculer_recette_modifiee()

    def retirer_ingredient(self):
        """Ouvre un dialogue pour choisir un ingrédient à retirer"""
        # Créer une liste des aliments actuellement dans la recette
        aliments_actuels = []
        for aliment in self.recette_modifiee["aliments"]:
            aliments_actuels.append(
                (
                    aliment["id"],
                    f"{aliment['nom']} ({aliment.get('marque', '')}) - {aliment['quantite']:.0f}g",
                )
            )

        # Si aucun aliment, afficher un message
        if not aliments_actuels:
            QMessageBox.information(
                self, "Aucun aliment", "Il n'y a pas d'aliments à retirer."
            )
            return

        # Créer un dialogue avec une liste des aliments
        dialog = QDialog(self)
        dialog.setWindowTitle("Retirer un aliment")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Sélectionnez l'aliment à retirer:"))

        list_widget = QListWidget()
        for aliment_id, aliment_nom in aliments_actuels:
            list_widget.addItem(aliment_nom)
            # Stocker l'ID comme donnée
            list_widget.item(list_widget.count() - 1).setData(Qt.UserRole, aliment_id)

        layout.addWidget(list_widget)

        # Boutons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(dialog.reject)

        btn_remove = QPushButton("Retirer")
        btn_remove.clicked.connect(dialog.accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_remove)
        layout.addLayout(btn_layout)

        # Exécuter le dialogue
        if dialog.exec():
            selected_item = list_widget.currentItem()
            if selected_item:
                aliment_id = selected_item.data(Qt.UserRole)

                # Ajouter à la liste des aliments exclus
                if aliment_id not in self.aliments_exclus:
                    self.aliments_exclus.append(aliment_id)

                # Trouver et supprimer le widget correspondant
                for i in range(self.scroll_layout.count()):
                    widget = self.scroll_layout.itemAt(i).widget()
                    if (
                        isinstance(widget, AlimentSliderWidget)
                        and widget.aliment_id == aliment_id
                    ):
                        widget.deleteLater()
                        break

                # Supprimer du dictionnaire des sliders
                if aliment_id in self.sliders:
                    del self.sliders[aliment_id]

                # Recalculer la recette modifiée
                self._calculer_recette_modifiee()

    def get_data(self):
        """Retourne les données pour appliquer la modification"""
        # Déterminer si on retourne les facteurs ou une liste d'ingrédients
        if self.nouveaux_aliments or self.aliments_exclus:
            # Cas d'une recette personnalisée (ingrédients ajoutés/supprimés)
            # Retourner la liste complète des ingrédients avec leurs quantités
            ingredients = []

            for aliment in self.recette_modifiee["aliments"]:
                ingredients.append(
                    {"id": aliment["id"], "quantite": aliment["quantite"]}
                )

            return ("personnalisee", ingredients)
        else:
            # Cas d'une recette standard avec facteurs
            return (self.recette_courante_id, self.facteurs_quantite)
