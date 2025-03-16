from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QLabel,
    QFrame,
    QGridLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt

from ..dialogs.repas_dialog import RepasDialog
from ..dialogs.aliment_repas_dialog import AlimentRepasDialog
from ..dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from ...utils.events import event_bus


class SemaineWidget(QWidget):
    """Widget représentant une semaine de planning"""

    def __init__(self, db_manager, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.semaine_id = semaine_id  # Identifiant numérique de la semaine
        self.setup_ui()
        self.load_data()

        # S'abonner aux événements de modification des aliments
        event_bus.aliment_supprime.connect(self.on_aliment_supprime)

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

    def on_aliment_supprime(self, aliment_id):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir les données de cette semaine
        self.load_data()
