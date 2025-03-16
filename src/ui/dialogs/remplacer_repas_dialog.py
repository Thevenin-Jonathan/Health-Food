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
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QFrame,
    QSplitter,
    QFormLayout,
    QScrollArea,
    QWidget,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal, Slot


class RemplacerRepasDialog(QDialog):
    """Dialogue pour remplacer un repas par une recette avec prévisualisation"""

    def __init__(self, parent=None, db_manager=None, repas_actuel=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.repas_actuel = repas_actuel
        self.facteurs_quantite = (
            {}
        )  # Stocke les facteurs d'ajustement pour chaque aliment

        # Récupérer les totaux de la journée actuelle
        self.jour_actuel = repas_actuel["jour"]
        self.semaine_id = repas_actuel.get("semaine_id")
        self.totaux_jour = self.calculer_totaux_jour()

        self.setup_ui()

    def calculer_totaux_jour(self):
        """Calcule les totaux nutritionnels de la journée actuelle"""
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)
        jour_repas = repas_semaine.get(self.jour_actuel, [])

        totaux = {"calories": 0, "proteines": 0, "glucides": 0, "lipides": 0}

        for repas in jour_repas:
            totaux["calories"] += repas["total_calories"]
            totaux["proteines"] += repas["total_proteines"]
            totaux["glucides"] += repas["total_glucides"]
            totaux["lipides"] += repas["total_lipides"]

        return totaux

    def setup_ui(self):
        self.setWindowTitle("Remplacer par une recette")
        self.setMinimumSize(
            1200, 900
        )  # Augmenté la taille minimale pour mieux accommoder 3 panneaux

        layout = QVBoxLayout()

        # En-tête avec le nom du repas actuel
        header = QLabel(f"<h2>Remplacer le repas \"{self.repas_actuel['nom']}\"</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Afficher le jour concerné
        jour_label = QLabel(f"<h3>Jour: {self.jour_actuel}</h3>")
        jour_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(jour_label)

        # Sélection de la recette
        recipe_form = QFormLayout()
        self.recette_combo = QComboBox()
        self.recette_combo.setMinimumWidth(400)
        self.charger_recettes()
        self.recette_combo.currentIndexChanged.connect(self.afficher_comparaison)
        recipe_form.addRow("Choisir une recette:", self.recette_combo)
        layout.addLayout(recipe_form)

        # Splitter principal pour diviser la vue en trois parties
        main_splitter = QSplitter(Qt.Horizontal)

        # Panneau gauche: Repas actuel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<h3>Repas actuel</h3>"))

        # Informations du repas actuel
        repas_actuel_frame = QFrame()
        repas_actuel_frame.setFrameShape(QFrame.StyledPanel)
        repas_actuel_layout = QVBoxLayout(repas_actuel_frame)

        # Nom et informations de base
        repas_actuel_layout.addWidget(QLabel(f"<b>{self.repas_actuel['nom']}</b>"))

        # Tableau des aliments du repas actuel
        self.repas_actuel_table = QTableWidget()
        self.repas_actuel_table.setColumnCount(3)
        self.repas_actuel_table.setHorizontalHeaderLabels(
            ["Aliment", "Quantité", "Calories"]
        )
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.repas_actuel_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        repas_actuel_layout.addWidget(self.repas_actuel_table)

        # Valeurs nutritionnelles du repas actuel
        self.repas_actuel_nutrition = QLabel()
        repas_actuel_layout.addWidget(QLabel("<h4>Valeurs nutritionnelles</h4>"))
        repas_actuel_layout.addWidget(self.repas_actuel_nutrition)

        left_layout.addWidget(repas_actuel_frame)

        # Panneau central: Recette sélectionnée
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("<h3>Recette sélectionnée</h3>"))

        # Informations de la recette
        self.recette_frame = QFrame()
        self.recette_frame.setFrameShape(QFrame.StyledPanel)
        self.recette_layout = QVBoxLayout(self.recette_frame)

        # Nom de la recette (sera défini lors de la sélection)
        self.recette_nom = QLabel()
        self.recette_layout.addWidget(self.recette_nom)

        # Zone défilante pour les ajustements d'ingrédients
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.ingredients_widget = QWidget()
        self.ingredients_layout = QVBoxLayout(self.ingredients_widget)
        scroll_area.setWidget(self.ingredients_widget)
        self.recette_layout.addWidget(scroll_area)

        # Valeurs nutritionnelles de la recette
        self.recette_nutrition = QLabel()
        self.recette_layout.addWidget(QLabel("<h4>Valeurs nutritionnelles</h4>"))
        self.recette_layout.addWidget(self.recette_nutrition)

        middle_layout.addWidget(self.recette_frame)

        # Panneau droit: Impacts et différences
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<h3>Impacts et différences</h3>"))

        # Section des impacts sur le repas
        repas_diff_frame = QFrame()
        repas_diff_frame.setFrameShape(QFrame.StyledPanel)
        repas_diff_layout = QVBoxLayout(repas_diff_frame)

        repas_diff_title = QLabel("<h4>Impact sur le repas</h4>")
        repas_diff_title.setAlignment(Qt.AlignCenter)
        repas_diff_layout.addWidget(repas_diff_title)

        # Tableau comparatif pour le repas
        repas_diff_table = QTableWidget()
        repas_diff_table.setRowCount(4)  # Calories, Protéines, Glucides, Lipides
        repas_diff_table.setColumnCount(3)  # Avant, Après, Différence
        repas_diff_table.setHorizontalHeaderLabels(["Actuel", "Nouveau", "Différence"])
        repas_diff_table.setVerticalHeaderLabels(
            ["Calories", "Protéines", "Glucides", "Lipides"]
        )

        # Configuration du tableau
        repas_diff_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        repas_diff_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        repas_diff_table.setEditTriggers(QTableWidget.NoEditTriggers)
        repas_diff_layout.addWidget(repas_diff_table)
        self.repas_diff_table = repas_diff_table

        # Labels pour les différences du repas
        repas_diff_box = QGroupBox("Résumé des différences")
        repas_diff_grid = QFormLayout(repas_diff_box)

        self.repas_cal_diff = QLabel("Calories: --")
        self.repas_prot_diff = QLabel("Protéines: --")
        self.repas_gluc_diff = QLabel("Glucides: --")
        self.repas_lip_diff = QLabel("Lipides: --")

        repas_diff_grid.addRow("", self.repas_cal_diff)
        repas_diff_grid.addRow("", self.repas_prot_diff)
        repas_diff_grid.addRow("", self.repas_gluc_diff)
        repas_diff_grid.addRow("", self.repas_lip_diff)

        repas_diff_layout.addWidget(repas_diff_box)
        right_layout.addWidget(repas_diff_frame)

        # Séparateur visuel
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(separator)

        # Section des impacts sur la journée
        jour_diff_frame = QFrame()
        jour_diff_frame.setFrameShape(QFrame.StyledPanel)
        jour_diff_layout = QVBoxLayout(jour_diff_frame)

        jour_diff_title = QLabel(f"<h4>Impact sur la journée ({self.jour_actuel})</h4>")
        jour_diff_title.setAlignment(Qt.AlignCenter)
        jour_diff_layout.addWidget(jour_diff_title)

        # Tableau comparatif des totaux journaliers
        jour_diff_table = QTableWidget()
        jour_diff_table.setRowCount(4)  # Calories, Protéines, Glucides, Lipides
        jour_diff_table.setColumnCount(3)  # Avant, Après, Différence
        jour_diff_table.setHorizontalHeaderLabels(["Avant", "Après", "Différence"])
        jour_diff_table.setVerticalHeaderLabels(
            ["Calories", "Protéines", "Glucides", "Lipides"]
        )

        # Configuration du tableau
        jour_diff_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        jour_diff_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        jour_diff_table.setEditTriggers(QTableWidget.NoEditTriggers)

        jour_diff_layout.addWidget(jour_diff_table)
        self.jour_diff_table = jour_diff_table

        # Résumé des différences pour la journée
        jour_diff_box = QGroupBox("Résumé des différences journalières")
        jour_diff_grid = QFormLayout(jour_diff_box)

        # Labels pour les différences de la journée
        self.jour_cal_diff = QLabel("Calories: --")
        self.jour_prot_diff = QLabel("Protéines: --")
        self.jour_gluc_diff = QLabel("Glucides: --")
        self.jour_lip_diff = QLabel("Lipides: --")

        jour_diff_grid.addRow("", self.jour_cal_diff)
        jour_diff_grid.addRow("", self.jour_prot_diff)
        jour_diff_grid.addRow("", self.jour_gluc_diff)
        jour_diff_grid.addRow("", self.jour_lip_diff)

        jour_diff_layout.addWidget(jour_diff_box)
        right_layout.addWidget(jour_diff_frame)

        # Ajouter les trois panneaux au splitter principal
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(middle_panel)
        main_splitter.addWidget(right_panel)

        # Répartir l'espace équitablement (avec un peu plus pour le panneau central)
        main_splitter.setSizes([300, 400, 300])

        layout.addWidget(
            main_splitter, 1
        )  # 1 = stretch factor pour prendre tout l'espace disponible

        # Boutons d'action
        btn_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_replace = QPushButton("Remplacer")
        self.btn_replace.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_replace)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Remplir les informations du repas actuel
        self.remplir_repas_actuel()

    def charger_recettes(self):
        """Charge les recettes disponibles dans le combobox"""
        self.recette_combo.clear()
        self.recettes = self.db_manager.get_repas_types()
        self.recette_ids = [recette["id"] for recette in self.recettes]

        # Ajouter un élément vide en premier
        self.recette_combo.addItem("-- Sélectionner une recette --")

        # Ajouter les recettes
        for recette in self.recettes:
            self.recette_combo.addItem(
                f"{recette['nom']} ({recette['total_calories']:.0f} kcal)"
            )

        # Déconnecter temporairement le signal pour éviter le déclenchement lors de l'initialisation
        self.recette_combo.blockSignals(True)
        self.recette_combo.setCurrentIndex(0)
        self.recette_combo.blockSignals(False)

    def remplir_repas_actuel(self):
        """Remplit le tableau avec les informations du repas actuel"""
        # Vider le tableau
        self.repas_actuel_table.setRowCount(0)

        # Remplir avec les aliments du repas actuel
        for i, aliment in enumerate(self.repas_actuel["aliments"]):
            self.repas_actuel_table.insertRow(i)

            # Nom de l'aliment
            self.repas_actuel_table.setItem(i, 0, QTableWidgetItem(aliment["nom"]))

            # Quantité
            self.repas_actuel_table.setItem(
                i, 1, QTableWidgetItem(f"{aliment['quantite']}g")
            )

            # Calories
            calories = aliment["calories"] * aliment["quantite"] / 100
            self.repas_actuel_table.setItem(
                i, 2, QTableWidgetItem(f"{calories:.0f} kcal")
            )

        # Informations nutritionnelles
        nutrition = (
            f"<b>Calories:</b> {self.repas_actuel['total_calories']:.0f} kcal<br>"
        )
        nutrition += (
            f"<b>Protéines:</b> {self.repas_actuel['total_proteines']:.1f}g<br>"
        )
        nutrition += f"<b>Glucides:</b> {self.repas_actuel['total_glucides']:.1f}g<br>"
        nutrition += f"<b>Lipides:</b> {self.repas_actuel['total_lipides']:.1f}g"
        self.repas_actuel_nutrition.setText(nutrition)

    def afficher_comparaison(self):
        """Affiche la comparaison entre le repas actuel et la recette sélectionnée"""
        index = self.recette_combo.currentIndex()

        # Si l'élément sélectionné est l'option par défaut (index 0), ne rien faire
        if index <= 0:
            # Réinitialiser les affichages
            self.recette_nom.setText("")

            # Vider le layout des ingrédients
            while self.ingredients_layout.count():
                item = self.ingredients_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            self.recette_nutrition.setText("")

            # Réinitialiser les tableaux et labels de différences
            self._reinitialiser_differences()
            return

        # Récupérer la recette sélectionnée (index - 1 car on a ajouté une option vide en premier)
        recette_id = self.recette_ids[index - 1]
        recette = self.db_manager.get_repas_type(
            recette_id
        )  # Récupérer la recette complète

        # Mettre à jour le nom de la recette
        self.recette_nom.setText(f"<b>{recette['nom']}</b>")

        # Réinitialiser les facteurs de quantité
        self.facteurs_quantite = {aliment["id"]: 1.0 for aliment in recette["aliments"]}

        # Vider le layout des ingrédients
        while self.ingredients_layout.count():
            item = self.ingredients_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Ajouter les ingrédients avec ajustement de quantité
        for aliment in recette["aliments"]:
            # Créer un groupe pour chaque aliment
            alim_group = QGroupBox(aliment["nom"])
            alim_layout = QFormLayout(alim_group)

            # Informations de base
            quantite_actuelle = aliment["quantite"]
            calories_base = aliment["calories"] * quantite_actuelle / 100

            # Slider pour ajuster la quantité (50% à 200%)
            slider_layout = QHBoxLayout()

            # Label pour la quantité (50%)
            slider_layout.addWidget(QLabel("50%"))

            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(50)
            slider.setMaximum(200)
            slider.setValue(100)
            slider.setTickInterval(25)
            slider.setTickPosition(QSlider.TicksBelow)
            slider.valueChanged.connect(
                lambda v, aid=aliment["id"]: self.ajuster_quantite(aid, v / 100)
            )
            slider_layout.addWidget(slider)

            # Label pour la quantité (200%)
            slider_layout.addWidget(QLabel("200%"))

            alim_layout.addRow("Ajuster:", slider_layout)

            # SpinBox pour la quantité exacte
            spin = QDoubleSpinBox()
            spin.setMinimum(quantite_actuelle * 0.5)
            spin.setMaximum(quantite_actuelle * 2.0)
            spin.setValue(quantite_actuelle)
            spin.setSuffix("g")
            spin.valueChanged.connect(
                lambda v, aid=aliment[
                    "id"
                ], base=quantite_actuelle: self.ajuster_quantite_absolue(aid, v, base)
            )
            alim_layout.addRow("Quantité:", spin)

            # Informations nutritionnelles de l'aliment
            info = (
                f"<b>Calories:</b> {calories_base:.0f} kcal | "
                f"<b>P:</b> {aliment['proteines'] * quantite_actuelle / 100:.1f}g | "
                f"<b>G:</b> {aliment['glucides'] * quantite_actuelle / 100:.1f}g | "
                f"<b>L:</b> {aliment['lipides'] * quantite_actuelle / 100:.1f}g"
            )
            info_label = QLabel(info)
            info_label.setObjectName(f"info_{aliment['id']}")
            alim_layout.addRow("Info:", info_label)

            self.ingredients_layout.addWidget(alim_group)

        # Calcul des valeurs nutritionnelles ajustées
        self.mettre_a_jour_valeurs_recette(recette)

    def ajuster_quantite(self, aliment_id, facteur):
        """Ajuste la quantité d'un ingrédient par un facteur"""
        self.facteurs_quantite[aliment_id] = facteur

        # Récupérer la recette pour mettre à jour les valeurs
        if self.recette_combo.currentIndex() >= 0:
            recette_id = self.recette_ids[self.recette_combo.currentIndex()]
            recette = self.db_manager.get_repas_type(recette_id)
            self.mettre_a_jour_valeurs_recette(recette)

    def ajuster_quantite_absolue(self, aliment_id, nouvelle_valeur, base_valeur):
        """Ajuste la quantité d'un ingrédient à une valeur absolue"""
        facteur = nouvelle_valeur / base_valeur
        self.facteurs_quantite[aliment_id] = facteur

        # Récupérer la recette pour mettre à jour les valeurs
        if self.recette_combo.currentIndex() >= 0:
            recette_id = self.recette_ids[self.recette_combo.currentIndex()]
            recette = self.db_manager.get_repas_type(recette_id)
            self.mettre_a_jour_valeurs_recette(recette)

    def mettre_a_jour_valeurs_recette(self, recette):
        """Met à jour les valeurs nutritionnelles de la recette avec les facteurs d'ajustement"""
        # Calculer les nouvelles valeurs nutritionnelles
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0

        for aliment in recette["aliments"]:
            facteur = self.facteurs_quantite.get(aliment["id"], 1.0)
            quantite_ajustee = aliment["quantite"] * facteur

            # Mettre à jour les infos de l'aliment si le widget existe
            info_label = self.findChild(QLabel, f"info_{aliment['id']}")
            if info_label:
                calories = aliment["calories"] * quantite_ajustee / 100
                proteines = aliment["proteines"] * quantite_ajustee / 100
                glucides = aliment["glucides"] * quantite_ajustee / 100
                lipides = aliment["lipides"] * quantite_ajustee / 100

                info = (
                    f"<b>Calories:</b> {calories:.0f} kcal | "
                    f"<b>P:</b> {proteines:.1f}g | "
                    f"<b>G:</b> {glucides:.1f}g | "
                    f"<b>L:</b> {lipides:.1f}g"
                )
                info_label.setText(info)

            # Ajouter aux totaux
            total_cal += aliment["calories"] * quantite_ajustee / 100
            total_prot += aliment["proteines"] * quantite_ajustee / 100
            total_gluc += aliment["glucides"] * quantite_ajustee / 100
            total_lip += aliment["lipides"] * quantite_ajustee / 100

        # Mettre à jour les valeurs nutritionnelles de la recette
        nutrition = f"<b>Calories:</b> {total_cal:.0f} kcal<br>"
        nutrition += f"<b>Protéines:</b> {total_prot:.1f}g<br>"
        nutrition += f"<b>Glucides:</b> {total_gluc:.1f}g<br>"
        nutrition += f"<b>Lipides:</b> {total_lip:.1f}g"
        self.recette_nutrition.setText(nutrition)

        # Mettre à jour les différences au niveau du repas
        diff_cal = total_cal - self.repas_actuel["total_calories"]
        diff_prot = total_prot - self.repas_actuel["total_proteines"]
        diff_gluc = total_gluc - self.repas_actuel["total_glucides"]
        diff_lip = total_lip - self.repas_actuel["total_lipides"]

        # Formater les différences du repas avec couleurs
        self.repas_cal_diff.setText(f"Calories: {self._format_diff(diff_cal, 'kcal')}")
        self.repas_prot_diff.setText(f"Protéines: {self._format_diff(diff_prot, 'g')}")
        self.repas_gluc_diff.setText(f"Glucides: {self._format_diff(diff_gluc, 'g')}")
        self.repas_lip_diff.setText(f"Lipides: {self._format_diff(diff_lip, 'g')}")

        # Remplir le tableau comparatif du repas
        # Calories
        self.repas_diff_table.setItem(
            0, 0, QTableWidgetItem(f"{self.repas_actuel['total_calories']:.0f} kcal")
        )
        self.repas_diff_table.setItem(0, 1, QTableWidgetItem(f"{total_cal:.0f} kcal"))
        diff_item = QTableWidgetItem(f"{self._format_diff_simple(diff_cal, 'kcal')}")
        self.set_diff_cell_color(diff_item, diff_cal)
        self.repas_diff_table.setItem(0, 2, diff_item)

        # Protéines
        self.repas_diff_table.setItem(
            1, 0, QTableWidgetItem(f"{self.repas_actuel['total_proteines']:.1f} g")
        )
        self.repas_diff_table.setItem(1, 1, QTableWidgetItem(f"{total_prot:.1f} g"))
        diff_item = QTableWidgetItem(f"{self._format_diff_simple(diff_prot, 'g')}")
        self.set_diff_cell_color(diff_item, diff_prot)
        self.repas_diff_table.setItem(1, 2, diff_item)

        # Glucides
        self.repas_diff_table.setItem(
            2, 0, QTableWidgetItem(f"{self.repas_actuel['total_glucides']:.1f} g")
        )
        self.repas_diff_table.setItem(2, 1, QTableWidgetItem(f"{total_gluc:.1f} g"))
        diff_item = QTableWidgetItem(f"{self._format_diff_simple(diff_gluc, 'g')}")
        self.set_diff_cell_color(diff_item, diff_gluc)
        self.repas_diff_table.setItem(2, 2, diff_item)

        # Lipides
        self.repas_diff_table.setItem(
            3, 0, QTableWidgetItem(f"{self.repas_actuel['total_lipides']:.1f} g")
        )
        self.repas_diff_table.setItem(3, 1, QTableWidgetItem(f"{total_lip:.1f} g"))
        diff_item = QTableWidgetItem(f"{self._format_diff_simple(diff_lip, 'g')}")
        self.set_diff_cell_color(diff_item, diff_lip)
        self.repas_diff_table.setItem(3, 2, diff_item)

        # Calculer l'impact sur les totaux journaliers
        jour_avant_cal = self.totaux_jour["calories"]
        jour_avant_prot = self.totaux_jour["proteines"]
        jour_avant_gluc = self.totaux_jour["glucides"]
        jour_avant_lip = self.totaux_jour["lipides"]

        jour_apres_cal = (
            jour_avant_cal - self.repas_actuel["total_calories"] + total_cal
        )
        jour_apres_prot = (
            jour_avant_prot - self.repas_actuel["total_proteines"] + total_prot
        )
        jour_apres_gluc = (
            jour_avant_gluc - self.repas_actuel["total_glucides"] + total_gluc
        )
        jour_apres_lip = jour_avant_lip - self.repas_actuel["total_lipides"] + total_lip

        # Remplir le tableau comparatif des journées
        # Calories
        self.jour_diff_table.setItem(
            0, 0, QTableWidgetItem(f"{jour_avant_cal:.0f} kcal")
        )
        self.jour_diff_table.setItem(
            0, 1, QTableWidgetItem(f"{jour_apres_cal:.0f} kcal")
        )
        diff_item = QTableWidgetItem(
            f"{self._format_diff_simple(jour_apres_cal - jour_avant_cal, 'kcal')}"
        )
        self.set_diff_cell_color(diff_item, jour_apres_cal - jour_avant_cal)
        self.jour_diff_table.setItem(0, 2, diff_item)

        # Protéines
        self.jour_diff_table.setItem(1, 0, QTableWidgetItem(f"{jour_avant_prot:.1f} g"))
        self.jour_diff_table.setItem(1, 1, QTableWidgetItem(f"{jour_apres_prot:.1f} g"))
        diff_item = QTableWidgetItem(
            f"{self._format_diff_simple(jour_apres_prot - jour_avant_prot, 'g')}"
        )
        self.set_diff_cell_color(diff_item, jour_apres_prot - jour_avant_prot)
        self.jour_diff_table.setItem(1, 2, diff_item)

        # Glucides
        self.jour_diff_table.setItem(2, 0, QTableWidgetItem(f"{jour_avant_gluc:.1f} g"))
        self.jour_diff_table.setItem(2, 1, QTableWidgetItem(f"{jour_apres_gluc:.1f} g"))
        diff_item = QTableWidgetItem(
            f"{self._format_diff_simple(jour_apres_gluc - jour_avant_gluc, 'g')}"
        )
        self.set_diff_cell_color(diff_item, jour_apres_gluc - jour_avant_gluc)
        self.jour_diff_table.setItem(2, 2, diff_item)

        # Lipides
        self.jour_diff_table.setItem(3, 0, QTableWidgetItem(f"{jour_avant_lip:.1f} g"))
        self.jour_diff_table.setItem(3, 1, QTableWidgetItem(f"{jour_apres_lip:.1f} g"))
        diff_item = QTableWidgetItem(
            f"{self._format_diff_simple(jour_apres_lip - jour_avant_lip, 'g')}"
        )
        self.set_diff_cell_color(diff_item, jour_apres_lip - jour_avant_lip)
        self.jour_diff_table.setItem(3, 2, diff_item)

        # Mettre à jour les différences de la journée
        self.jour_cal_diff.setText(
            f"Calories: {self._format_diff(jour_apres_cal - jour_avant_cal, 'kcal')}"
        )
        self.jour_prot_diff.setText(
            f"Protéines: {self._format_diff(jour_apres_prot - jour_avant_prot, 'g')}"
        )
        self.jour_gluc_diff.setText(
            f"Glucides: {self._format_diff(jour_apres_gluc - jour_avant_gluc, 'g')}"
        )
        self.jour_lip_diff.setText(
            f"Lipides: {self._format_diff(jour_apres_lip - jour_avant_lip, 'g')}"
        )

    def set_diff_cell_color(self, item, diff):
        """Définit la couleur de fond d'une cellule de différence"""
        if diff > 0:
            item.setForeground(Qt.red)
        elif diff < 0:
            item.setForeground(Qt.darkGreen)
        else:
            item.setForeground(Qt.gray)

    def _format_diff_simple(self, diff, unite):
        """Formate une différence avec signe mais sans HTML"""
        if diff > 0:
            return f"+{diff:.1f} {unite}"
        elif diff < 0:
            return f"{diff:.1f} {unite}"
        else:
            return f"0 {unite}"

    def _format_diff(self, diff, unite):
        """Formate une différence avec couleur et signe"""
        if diff > 0:
            return f"<span style='color: red'>+{diff:.1f}{unite}</span>"
        elif diff < 0:
            return f"<span style='color: green'>{diff:.1f}{unite}</span>"
        else:
            return f"<span style='color: gray'>0{unite}</span>"

    def _reinitialiser_differences(self):
        """Réinitialise tous les éléments d'affichage des différences"""
        # Réinitialiser les labels de différence pour le repas
        self.repas_cal_diff.setText("Calories: --")
        self.repas_prot_diff.setText("Protéines: --")
        self.repas_gluc_diff.setText("Glucides: --")
        self.repas_lip_diff.setText("Lipides: --")

        # Réinitialiser le tableau des différences du repas
        for row in range(4):  # 4 lignes: calories, protéines, glucides, lipides
            for col in range(3):  # 3 colonnes: actuel, nouveau, différence
                if col == 0:  # Colonne "Actuel" - garder les valeurs actuelles
                    if row == 0:  # Calories
                        self.repas_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(
                                f"{self.repas_actuel['total_calories']:.0f} kcal"
                            ),
                        )
                    elif row == 1:  # Protéines
                        self.repas_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(
                                f"{self.repas_actuel['total_proteines']:.1f} g"
                            ),
                        )
                    elif row == 2:  # Glucides
                        self.repas_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(
                                f"{self.repas_actuel['total_glucides']:.1f} g"
                            ),
                        )
                    elif row == 3:  # Lipides
                        self.repas_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(
                                f"{self.repas_actuel['total_lipides']:.1f} g"
                            ),
                        )
                else:  # Colonnes "Nouveau" et "Différence"
                    self.repas_diff_table.setItem(row, col, QTableWidgetItem("--"))

        # Réinitialiser les labels de différence pour la journée
        self.jour_cal_diff.setText("Calories: --")
        self.jour_prot_diff.setText("Protéines: --")
        self.jour_gluc_diff.setText("Glucides: --")
        self.jour_lip_diff.setText("Lipides: --")

        # Réinitialiser le tableau des différences de la journée
        for row in range(4):  # 4 lignes: calories, protéines, glucides, lipides
            for col in range(3):  # 3 colonnes: avant, après, différence
                if col == 0:  # Colonne "Avant" - garder les valeurs actuelles
                    if row == 0:  # Calories
                        self.jour_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(
                                f"{self.totaux_jour['calories']:.0f} kcal"
                            ),
                        )
                    elif row == 1:  # Protéines
                        self.jour_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(f"{self.totaux_jour['proteines']:.1f} g"),
                        )
                    elif row == 2:  # Glucides
                        self.jour_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(f"{self.totaux_jour['glucides']:.1f} g"),
                        )
                    elif row == 3:  # Lipides
                        self.jour_diff_table.setItem(
                            row,
                            col,
                            QTableWidgetItem(f"{self.totaux_jour['lipides']:.1f} g"),
                        )
                else:  # Colonnes "Après" et "Différence"
                    self.jour_diff_table.setItem(row, col, QTableWidgetItem("--"))

    def get_data(self):
        """Retourne l'ID de la recette sélectionnée et les facteurs d'ajustement"""
        index = self.recette_combo.currentIndex()
        if index > 0:  # Si une recette est sélectionnée (pas l'élément vide)
            recette_id = self.recette_ids[index - 1]  # Ajustement pour l'élément vide
            return recette_id, self.facteurs_quantite
        return None, {}
