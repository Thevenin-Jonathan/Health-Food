from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QLabel,
    QDialog,
    QComboBox,
    QSpinBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QTabWidget,
    QInputDialog,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor

from ..dialogs.remplacer_repas_dialog import RemplacerRepasDialog


class PlanningTab(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

        # Dictionnaire pour stocker les widgets des semaines
        self.semaines = {}

        # Compteur pour les nouvelles semaines
        self.semaine_counter = 1

        # Liste pour suivre les numéros de semaine utilisés
        self.semaine_ids = []

        # Dictionnaire pour stocker les noms personnalisés des onglets
        self.onglets_personnalises = {}

        self.setup_ui()
        self.ajouter_semaine()  # Ajouter la première semaine par défaut

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Panel de contrôle des semaines
        control_layout = QHBoxLayout()

        self.btn_add_week = QPushButton("Ajouter une semaine")
        self.btn_add_week.clicked.connect(self.ajouter_semaine)
        control_layout.addWidget(self.btn_add_week)

        self.btn_remove_week = QPushButton("Supprimer la semaine courante")
        self.btn_remove_week.clicked.connect(self.supprimer_semaine_courante)
        control_layout.addWidget(self.btn_remove_week)

        # Ajout du bouton pour renommer la semaine courante
        self.btn_rename_week = QPushButton("Renommer la semaine courante")
        self.btn_rename_week.clicked.connect(self.renommer_semaine_courante)
        control_layout.addWidget(self.btn_rename_week)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Onglets pour les semaines
        self.tabs_semaines = QTabWidget()
        self.tabs_semaines.setTabsClosable(True)
        self.tabs_semaines.tabCloseRequested.connect(self.fermer_semaine)
        self.tabs_semaines.currentChanged.connect(self.on_tab_changed)

        # Permettre le glisser-déposer des onglets
        self.tabs_semaines.setMovable(True)

        # Connecter le signal de déplacement d'onglet
        self.tabs_semaines.tabBar().tabMoved.connect(self.on_tab_moved)

        main_layout.addWidget(self.tabs_semaines, 1)

        # Bouton pour ajouter un repas
        self.btn_add_meal = QPushButton("Ajouter un repas")
        self.btn_add_meal.clicked.connect(self.add_meal)
        main_layout.addWidget(self.btn_add_meal)

        self.setLayout(main_layout)

    def on_tab_changed(self, index):
        """Méthode appelée quand l'onglet actif change"""
        # Activer/désactiver les boutons en fonction de si un onglet est sélectionné
        has_tab = index >= 0
        self.btn_remove_week.setEnabled(has_tab)
        self.btn_rename_week.setEnabled(has_tab)
        self.btn_add_meal.setEnabled(has_tab)

    def on_tab_moved(self, from_index, to_index):
        """Méthode appelée lorsqu'un onglet est déplacé"""
        # Mettre à jour les noms d'onglets pour refléter l'ordre actuel
        self.mettre_a_jour_noms_onglets()

    def ajouter_semaine(self):
        """Ajoute une nouvelle semaine numérotée"""
        # Trouver le prochain numéro de semaine disponible
        semaine_id = 1

        # Si on a déjà des semaines, trouver le premier ID non utilisé
        if self.semaine_ids:
            # Trouver le premier numéro disponible dans la séquence
            for i in range(1, max(self.semaine_ids) + 2):
                if i not in self.semaine_ids:
                    semaine_id = i
                    break

        # Créer un widget pour cette semaine
        semaine_widget = SemaineWidget(self.db_manager, semaine_id)

        # Ajouter l'onglet
        # Plutôt que d'utiliser l'ID comme numéro, utiliser la position + 1
        position = self.tabs_semaines.count() + 1
        tab_text = f"Semaine {position}"
        index = self.tabs_semaines.addTab(semaine_widget, tab_text)

        # Stocker le widget dans le dictionnaire
        self.semaines[semaine_id] = semaine_widget

        # Ajouter l'ID à la liste des semaines utilisées
        self.semaine_ids.append(semaine_id)

        # Passer à cet onglet
        self.tabs_semaines.setCurrentIndex(index)

        # Mettre à jour l'état des boutons
        self.on_tab_changed(index)

        # Mettre à jour les noms d'onglets si nécessaire pour garantir la cohérence
        self.mettre_a_jour_noms_onglets()

    def fermer_semaine(self, index):
        """Ferme une semaine à l'index donné"""
        # Si c'est la dernière semaine, ne pas permettre la fermeture
        if self.tabs_semaines.count() <= 1:
            QMessageBox.warning(
                self, "Impossible", "Vous devez garder au moins une semaine."
            )
            return

        # Trouver l'ID de semaine correspondant à cet onglet
        semaine_widget = self.tabs_semaines.widget(index)
        # Trouver la clé (ID) correspondant à ce widget
        semaine_id = None
        for id, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = id
                break

        if semaine_id is not None:
            # Supprimer l'ID de la liste des semaines utilisées
            self.semaine_ids.remove(semaine_id)

            # Supprimer tout nom personnalisé pour cet onglet
            if semaine_id in self.onglets_personnalises:
                del self.onglets_personnalises[semaine_id]

            # Supprimer du dictionnaire
            del self.semaines[semaine_id]

            # Supprimer l'onglet
            self.tabs_semaines.removeTab(index)

            # Mettre à jour les noms d'onglets par défaut
            self.mettre_a_jour_noms_onglets()

    def supprimer_semaine_courante(self):
        """Supprime la semaine actuellement affichée"""
        current_index = self.tabs_semaines.currentIndex()
        self.fermer_semaine(current_index)

    def renommer_semaine_courante(self):
        """Ouvre un dialogue pour renommer la semaine courante"""
        current_index = self.tabs_semaines.currentIndex()
        if current_index < 0:
            return

        # Trouver l'ID de la semaine courante
        semaine_widget = self.tabs_semaines.widget(current_index)
        semaine_id = None
        for id, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = id
                break

        if semaine_id is not None:
            # Récupérer le nom actuel
            nom_actuel = self.tabs_semaines.tabText(current_index)

            # Ouvrir une boîte de dialogue pour saisir le nouveau nom
            nouveau_nom, ok = QInputDialog.getText(
                self,
                "Renommer la semaine",
                "Entrez un nouveau nom pour cette semaine:",
                QLineEdit.Normal,
                nom_actuel,
            )

            if ok and nouveau_nom:
                # Enregistrer le nouveau nom personnalisé
                self.onglets_personnalises[semaine_id] = nouveau_nom

                # Mettre à jour l'onglet
                self.tabs_semaines.setTabText(current_index, nouveau_nom)

    def mettre_a_jour_noms_onglets(self):
        """Met à jour les noms des onglets non personnalisés en fonction de leur position réelle"""
        position_counter = 1  # Compteur pour les onglets non personnalisés

        # Créer un mapping temporaire entre l'index d'onglet et l'ID de semaine
        index_to_id = {}
        for index in range(self.tabs_semaines.count()):
            semaine_widget = self.tabs_semaines.widget(index)
            for id, widget in self.semaines.items():
                if widget == semaine_widget:
                    index_to_id[index] = id
                    break

        # Mettre à jour les noms des onglets non personnalisés
        for index in range(self.tabs_semaines.count()):
            if index in index_to_id:
                semaine_id = index_to_id[index]
                if semaine_id not in self.onglets_personnalises:
                    # Onglet non personnalisé, utiliser la numérotation séquentielle
                    self.tabs_semaines.setTabText(index, f"Semaine {position_counter}")
                    position_counter += 1

    def add_meal(self):
        """Ajoute un repas à la semaine courante"""
        current_semaine_widget = self.tabs_semaines.currentWidget()
        if current_semaine_widget:
            current_semaine_widget.add_meal()


class SemaineWidget(QWidget):
    """Widget représentant une semaine de planning"""

    def __init__(self, db_manager, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.semaine_id = semaine_id  # Identifiant numérique de la semaine
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Conteneur pour les jours avec scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget contenant les jours
        self.days_container = QWidget()
        self.days_layout = QGridLayout()

        # Définir une largeur maximum pour les colonnes des jours
        self.days_layout.setColumnMinimumWidth(0, 300)  # Largeur minimum
        self.days_layout.setColumnStretch(0, 1)  # Facteur d'étirement

        self.days_container.setLayout(self.days_layout)

        self.scroll_area.setWidget(self.days_container)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

    def load_data(self):
        # Nettoyer la disposition existante
        while self.days_layout.count():
            item = self.days_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Récupérer les données des repas pour la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)

        jours = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]

        for col, jour in enumerate(jours):
            # Créer un widget pour le jour
            day_widget = QWidget()
            day_widget.setMaximumWidth(
                350
            )  # Ajouter cette ligne pour limiter la largeur
            day_layout = QVBoxLayout()
            day_widget.setLayout(day_layout)

            # Titre du jour
            titre_jour = QLabel(f"<h2>{jour}</h2>")
            titre_jour.setAlignment(Qt.AlignCenter)
            day_layout.addWidget(titre_jour)

            # Ajouter les repas du jour
            total_cal = 0
            total_prot = 0
            total_gluc = 0
            total_lip = 0

            for repas in repas_semaine[jour]:
                # Créer un widget pour le repas
                repas_widget = QFrame()
                repas_widget.setFrameShape(QFrame.StyledPanel)
                repas_widget.setFrameShadow(QFrame.Raised)
                repas_layout = QVBoxLayout()
                repas_widget.setLayout(repas_layout)

                # Titre du repas avec boutons
                repas_header = QHBoxLayout()
                repas_title = QLabel(f"<h3>{repas['nom']}</h3>")
                repas_header.addWidget(repas_title)
                repas_header.addStretch()  # Ajouter un espace extensible pour pousser les boutons à droite

                # Bouton pour ajouter des aliments
                btn_add = QPushButton("+")
                btn_add.setFixedSize(24, 24)  # Taille fixe pour cohérence
                btn_add.setStyleSheet(
                    """
                    QPushButton { 
                        color: white; 
                        background-color: #4CAF50; 
                        font-weight: bold; 
                        font-size: 16px;
                        padding: 0px;
                        margin: 0px;
                    }
                    QPushButton:hover { 
                        background-color: #45a049; 
                    }
                """
                )
                btn_add.setToolTip("Ajouter un aliment à ce repas")
                btn_add.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.add_food_to_meal(r_id)
                )

                # Bouton pour remplacer le repas par une recette
                btn_replace = QPushButton("⇄")
                btn_replace.setFixedSize(24, 24)
                btn_replace.setStyleSheet(
                    """
                    QPushButton { 
                        color: white; 
                        background-color: #3498db; 
                        font-weight: bold; 
                        font-size: 12px;
                        padding: 0px;
                        margin: 0px;
                    }
                    QPushButton:hover { 
                        background-color: #2980b9; 
                    }
                """
                )
                btn_replace.setToolTip("Remplacer par une recette")
                btn_replace.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.remplacer_repas_par_recette(
                        r_id
                    )
                )

                # Bouton pour supprimer le repas (croix rouge simplifiée)
                btn_delete = QPushButton("×")
                btn_delete.setFixedSize(24, 24)
                btn_delete.setStyleSheet(
                    """
                    QPushButton { 
                        color: white; 
                        background-color: #e74c3c; 
                        font-weight: bold; 
                        font-size: 16px;
                        padding: 0px;
                    }
                    QPushButton:hover { 
                        background-color: #c0392b; 
                    }
                """
                )
                btn_delete.setToolTip("Supprimer ce repas")
                btn_delete.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.delete_meal(r_id)
                )

                # Ajouter les boutons directement au layout sans conteneurs supplémentaires
                repas_header.addWidget(btn_add)
                repas_header.addWidget(btn_replace)
                repas_header.addWidget(btn_delete)
                repas_layout.addLayout(repas_header)

                # Ajouter les aliments du repas
                if repas["aliments"]:
                    for aliment in repas["aliments"]:
                        alim_layout = QHBoxLayout()

                        # Texte de base de l'aliment
                        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
                        alim_label = QLabel(alim_text)
                        alim_label.setWordWrap(True)
                        alim_layout.addWidget(alim_label)
                        alim_layout.addStretch()  # Ajouter un espace extensible

                        # Ajouter un tooltip avec les informations détaillées des macros
                        # Calculer les valeurs nutritionnelles en fonction du poids
                        calories = aliment["calories"] * aliment["quantite"] / 100
                        proteines = aliment["proteines"] * aliment["quantite"] / 100
                        glucides = aliment["glucides"] * aliment["quantite"] / 100
                        lipides = aliment["lipides"] * aliment["quantite"] / 100

                        # Créer un tooltip riche avec les informations détaillées
                        tooltip_text = f"""<b>{aliment['nom']}</b> ({aliment['quantite']}g)<br>
                                        <b>Calories:</b> {calories:.0f} kcal<br>
                                        <b>Protéines:</b> {proteines:.1f}g<br>
                                        <b>Glucides:</b> {glucides:.1f}g<br>
                                        <b>Lipides:</b> {lipides:.1f}g"""

                        if "fibres" in aliment and aliment["fibres"]:
                            fibres = aliment["fibres"] * aliment["quantite"] / 100
                            tooltip_text += f"<br><b>Fibres:</b> {fibres:.1f}g"

                        alim_label.setToolTip(tooltip_text)

                        # Bouton pour supprimer l'aliment (croix rouge simplifiée)
                        btn_remove = QPushButton("×")
                        btn_remove.setFixedSize(20, 20)  # Plus petit pour les aliments
                        btn_remove.setStyleSheet(
                            """
                            QPushButton { 
                                color: white; 
                                background-color: #e74c3c; 
                                font-weight: bold; 
                                font-size: 12px;
                                padding: 0px;
                            }
                            QPushButton:hover { 
                                background-color: #c0392b; 
                            }
                        """
                        )
                        btn_remove.setToolTip("Supprimer cet aliment")
                        btn_remove.clicked.connect(
                            lambda checked, r_id=repas["id"], a_id=aliment[
                                "id"
                            ]: self.remove_food_from_meal(r_id, a_id)
                        )

                        # Ajouter le bouton directement sans conteneur
                        alim_layout.addWidget(btn_remove)

                        repas_layout.addLayout(alim_layout)
                else:
                    repas_layout.addWidget(QLabel("Aucun aliment"))

                # Afficher les totaux du repas
                repas_layout.addWidget(
                    QLabel(
                        f"<b>Total:</b> {repas['total_calories']:.0f} kcal | "
                        f"P: {repas['total_proteines']:.1f}g | "
                        f"G: {repas['total_glucides']:.1f}g | "
                        f"L: {repas['total_lipides']:.1f}g"
                    )
                )

                day_layout.addWidget(repas_widget)

                # Ajouter aux totaux du jour
                total_cal += repas["total_calories"]
                total_prot += repas["total_proteines"]
                total_gluc += repas["total_glucides"]
                total_lip += repas["total_lipides"]

            # Afficher les totaux du jour
            total_widget = QFrame()
            total_widget.setFrameShape(QFrame.StyledPanel)
            total_widget.setProperty("class", "day-total")
            total_layout = QVBoxLayout()
            total_widget.setLayout(total_layout)

            total_layout.addWidget(QLabel(f"<h3>Total du jour</h3>"))
            total_layout.addWidget(QLabel(f"<b>Calories:</b> {total_cal:.0f} kcal"))
            total_layout.addWidget(QLabel(f"<b>Protéines:</b> {total_prot:.1f}g"))
            total_layout.addWidget(QLabel(f"<b>Glucides:</b> {total_gluc:.1f}g"))
            total_layout.addWidget(QLabel(f"<b>Lipides:</b> {total_lip:.1f}g"))

            day_layout.addWidget(total_widget)
            day_layout.addStretch()

            self.days_layout.addWidget(day_widget, 0, col)

        # Ajouter ce code ici, après la boucle qui crée les colonnes
        for col in range(7):  # Pour chaque jour
            self.days_layout.setColumnStretch(col, 1)  # Répartition égale

    def add_meal(self):
        """Ajoute un repas à cette semaine"""
        dialog = RepasDialog(self, self.db_manager, self.semaine_id)
        if dialog.exec():
            nom, jour, ordre, repas_type_id = dialog.get_data()

            if repas_type_id:
                # Utiliser une recette existante
                self.db_manager.appliquer_repas_type_au_jour(
                    repas_type_id, jour, ordre, self.semaine_id
                )
            else:
                # Créer un nouveau repas vide
                self.db_manager.ajouter_repas(nom, jour, ordre, self.semaine_id)

            self.load_data()

    def add_food_to_meal(self, repas_id):
        dialog = AlimentRepasDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()
            self.db_manager.ajouter_aliment_repas(repas_id, aliment_id, quantite)
            self.load_data()

    def delete_meal(self, repas_id):
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_repas(repas_id)
            self.load_data()

    def remove_food_from_meal(self, repas_id, aliment_id):
        """Supprimer un aliment d'un repas"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet aliment du repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_aliment_repas(repas_id, aliment_id)
            self.load_data()

    def remplacer_repas_par_recette(self, repas_id):
        """Remplace un repas existant par une recette avec prévisualisation des différences"""
        # Récupérer les informations du repas actuel
        repas_actuel = None
        for jour, repas_list in self.db_manager.get_repas_semaine(
            self.semaine_id
        ).items():
            for repas in repas_list:
                if repas["id"] == repas_id:
                    repas_actuel = repas
                    break
            if repas_actuel:
                break

        if not repas_actuel:
            return

        # Ouvrir le dialogue de comparaison et remplacement
        dialog = RemplacerRepasDialog(self, self.db_manager, repas_actuel)
        if dialog.exec():
            recette_id, facteurs_ou_ingredients = dialog.get_data()

            # Supprimer l'ancien repas
            self.db_manager.supprimer_repas(repas_id)

            if recette_id == "personnalisee":
                # Traiter le cas d'une recette personnalisée (où des ingrédients ont été ajoutés/supprimés)
                self.db_manager.appliquer_recette_modifiee_au_jour(
                    dialog.recette_courante_id,  # ID de la recette de base
                    facteurs_ou_ingredients,  # Liste des ingrédients avec quantités ajustées
                    repas_actuel["jour"],
                    repas_actuel["ordre"],
                    self.semaine_id,
                )
            else:
                # Créer un nouveau repas basé sur la recette avec les quantités ajustées
                self.db_manager.appliquer_repas_type_au_jour_avec_facteurs(
                    recette_id,
                    repas_actuel["jour"],
                    repas_actuel["ordre"],
                    self.semaine_id,
                    facteurs_ou_ingredients,
                )

            # Actualiser l'affichage
            self.load_data()


class RepasDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, semaine_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.semaine_id = semaine_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un repas")
        self.setMinimumWidth(300)

        layout = QFormLayout()

        # Option pour choisir entre un nouveau repas ou une recette existante
        self.type_choix = QComboBox()
        self.type_choix.addItems(["Nouveau repas", "Utiliser une recette existante"])
        self.type_choix.currentIndexChanged.connect(self.toggle_mode)
        layout.addRow("Type:", self.type_choix)

        # Widget pour contenir les champs spécifiques au mode
        self.mode_widget = QWidget()
        self.mode_layout = QFormLayout(self.mode_widget)

        # Mode nouveau repas
        self.nom_input = QLineEdit()
        self.mode_layout.addRow("Nom du repas:", self.nom_input)

        # Mode recette
        self.recette_combo = QComboBox()
        self.recette_combo.hide()
        self.charger_recettes()
        self.mode_layout.addRow("Recette:", self.recette_combo)

        layout.addRow(self.mode_widget)

        # Sélection du jour (commun aux deux modes)
        self.jour_input = QComboBox()
        self.jour_input.addItems(
            ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        )
        layout.addRow("Jour:", self.jour_input)

        # Ordre dans la journée (commun aux deux modes) - Avec style amélioré
        self.ordre_input = QSpinBox()
        self.ordre_input.setMinimum(1)
        self.ordre_input.setValue(1)
        self.ordre_input.setFixedHeight(30)  # Augmenter la hauteur
        self.ordre_input.setStyleSheet(
            """
            QSpinBox { 
                padding-right: 15px; /* Espace pour les flèches */
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px; /* Augmenter la largeur des boutons */
                height: 14px; /* Définir la hauteur des boutons */
                padding: 0px;
            }
            QSpinBox::up-button {
                subcontrol-position: top right;
            }
            QSpinBox::down-button {
                subcontrol-position: bottom right;
            }
        """
        )
        layout.addRow("Ordre:", self.ordre_input)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.validate_and_accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

        # Initialiser le mode
        self.toggle_mode(0)

    def charger_recettes(self):
        """Charge les recettes disponibles dans le combobox"""
        if not self.db_manager:
            return

        self.recette_combo.clear()
        self.recettes = self.db_manager.get_repas_types()

        self.recette_ids = [recette["id"] for recette in self.recettes]

        for recette in self.recettes:
            self.recette_combo.addItem(recette["nom"])

    def toggle_mode(self, index):
        """Change le mode entre nouveau repas et recette existante"""
        if index == 0:  # Nouveau repas
            self.nom_input.show()
            self.recette_combo.hide()
        else:  # Recette existante
            self.nom_input.hide()
            self.recette_combo.show()

    def validate_and_accept(self):
        """Valide les données avant d'accepter"""
        if self.type_choix.currentIndex() == 0 and not self.nom_input.text().strip():
            QMessageBox.warning(
                self, "Champ obligatoire", "Le nom du repas est obligatoire."
            )
            return
        elif self.type_choix.currentIndex() == 1 and self.recette_combo.count() == 0:
            QMessageBox.warning(
                self,
                "Aucune recette",
                "Aucune recette disponible. Veuillez en créer une d'abord.",
            )
            return

        self.accept()

    def get_data(self):
        """Retourne les données du formulaire"""
        if self.type_choix.currentIndex() == 0:
            # Nouveau repas
            return (
                self.nom_input.text().strip(),
                self.jour_input.currentText(),
                self.ordre_input.value(),
                None,  # Pas de recette sélectionnée
            )
        else:
            # Recette existante
            if self.recette_combo.count() > 0:
                recette_id = self.recette_ids[self.recette_combo.currentIndex()]
                return (
                    None,  # Pas besoin de nom, on utilise celui de la recette
                    self.jour_input.currentText(),
                    self.ordre_input.value(),
                    recette_id,
                )
            return (None, None, None, None)


class AlimentRepasDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un aliment au repas")
        self.setMinimumWidth(350)

        layout = QFormLayout()

        # Sélection de l'aliment
        self.aliment_combo = QComboBox()
        self.load_aliments()
        layout.addRow("Aliment:", self.aliment_combo)

        # Quantité en grammes avec style amélioré pour une meilleure manipulation
        self.quantite_input = QDoubleSpinBox()
        self.quantite_input.setMinimum(1)
        self.quantite_input.setMaximum(5000)
        self.quantite_input.setValue(100)
        self.quantite_input.setSuffix(" g")
        # Configuration pour une meilleure utilisation des flèches
        self.quantite_input.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
        self.quantite_input.setSingleStep(10)  # Incrément de 10g par défaut
        self.quantite_input.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        # Style pour les boutons verticaux
        self.quantite_input.setStyleSheet(
            """
            QDoubleSpinBox {
                padding-right: 5px;
            }
            QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 15px;
            }
            QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 15px;
            }
        """
        )
        layout.addRow("Quantité:", self.quantite_input)

        # Informations sur l'aliment sélectionné
        self.info_label = QLabel("Sélectionnez un aliment pour voir ses informations")
        layout.addRow(self.info_label)

        # Mettre à jour les informations quand on change d'aliment
        self.aliment_combo.currentIndexChanged.connect(self.update_info)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Ajouter")
        self.btn_save.clicked.connect(self.validate_and_accept)

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

            info_text = f"<b>Calories:</b> {aliment['calories']} kcal/100g | "
            info_text += f"<b>P:</b> {aliment['proteines']}g | "
            info_text += f"<b>G:</b> {aliment['glucides']}g | "
            info_text += f"<b>L:</b> {aliment['lipides']}g"

            self.info_label.setText(info_text)

    def validate_and_accept(self):
        if self.aliment_combo.currentIndex() < 0:
            QMessageBox.warning(
                self, "Sélection requise", "Veuillez sélectionner un aliment."
            )
            return

        self.accept()

    def get_data(self):
        aliment_id = self.aliment_ids[self.aliment_combo.currentIndex()]
        return (aliment_id, self.quantite_input.value())


class GestionAlimentsRepasDialog(QDialog):
    """Dialogue pour gérer les aliments d'un repas (supprimer)"""

    def __init__(self, parent=None, db_manager=None, repas_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.repas_id = repas_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Gérer les aliments du repas")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()

        # Liste des aliments du repas
        self.liste_aliments = QListWidget()
        self.liste_aliments.setContextMenuPolicy(Qt.CustomContextMenu)
        self.liste_aliments.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.liste_aliments)

        # Charger les aliments
        self.load_aliments()

        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_aliments(self):
        """Charge les aliments du repas dans la liste"""
        self.liste_aliments.clear()

        aliments = self.db_manager.get_aliments_repas(self.repas_id)

        for aliment in aliments:
            item_text = f"{aliment['nom']} - {aliment['quantite']}g ({aliment['calories'] * aliment['quantite'] / 100:.0f} kcal)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, aliment)
            self.liste_aliments.addItem(item)

    def show_context_menu(self, position):
        """Affiche le menu contextuel pour supprimer un aliment"""
        item = self.liste_aliments.itemAt(position)

        if item:
            menu = QMenu()
            supprimer_action = menu.addAction("Supprimer")

            action = menu.exec_(self.liste_aliments.mapToGlobal(position))

            if action == supprimer_action:
                aliment_data = item.data(Qt.UserRole)
                self.supprimer_aliment(aliment_data["id"])

    def supprimer_aliment(self, aliment_id):
        """Supprime un aliment du repas"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet aliment du repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_aliment_repas(self.repas_id, aliment_id)
            self.load_aliments()
