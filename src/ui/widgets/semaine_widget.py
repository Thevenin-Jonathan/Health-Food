from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QGridLayout,
)

from src.utils import EVENT_BUS
from src.utils import JOURS_SEMAINE
from src.ui.widgets.jour_widget import JourWidget
from .print_manager import PrintManager


class SemaineWidget(QWidget):
    """Widget représentant une semaine de planning"""

    def __init__(self, db_manager, semaine_id):
        """
        Configure la disposition principale des widgets.
        """
        super().__init__()
        self.db_manager = db_manager
        self.semaine_id = semaine_id  # Identifiant numérique de la semaine
        self.print_manager = PrintManager(self.db_manager)

        # Charger les objectifs utilisateur dès l'initialisation
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()

        # Liste de widgets jour pour référence
        self.jour_widgets = []

        # Dictionnaire pour suivre les recettes utilisées dans cette semaine
        self.recettes_utilisees = {}

        self.setup_ui()
        self.load_data()

        # S'abonner aux événements
        EVENT_BUS.utilisateur_modifie.connect(self.update_objectifs_utilisateur)
        EVENT_BUS.aliment_supprime.connect(self.on_aliment_supprime)
        EVENT_BUS.repas_modifies.connect(self.on_repas_modifies)
        EVENT_BUS.recette_modifiee.connect(self.on_recette_modifiee)

    def setup_ui(self):
        # Dictionnaire pour suivre les recettes utilisées dans cette semaine
        self.recettes_utilisees = {}

        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)  # Réduire l'espacement vertical entre éléments
        main_layout.setContentsMargins(
            5, 5, 5, 5
        )  # Réduire les marges autour du widget principal

        # Conteneur pour les jours avec scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)

        # Widget contenant les jours
        self.days_container = QWidget()
        self.days_layout = QGridLayout()
        self.days_layout.setSpacing(5)  # Réduire l'espacement entre les jours
        self.days_layout.setContentsMargins(
            2, 2, 2, 2
        )  # Réduire les marges du conteneur

        # Définir la même largeur minimum pour TOUTES les colonnes
        for col in range(len(JOURS_SEMAINE)):
            self.days_layout.setColumnMinimumWidth(
                col, 280
            )  # Même largeur minimum pour tous les jours
            self.days_layout.setColumnStretch(
                col, 1
            )  # Même facteur d'étirement pour tous

        self.days_container.setLayout(self.days_layout)

        self.scroll_area.setWidget(self.days_container)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

    def load_data(self):
        """
        Charge les données des repas pour la semaine et crée les widgets jour correspondants.
        Cette méthode nettoie d'abord l'interface existante avant de recharger toutes les données.
        """
        # Nettoyer la disposition existante
        while self.days_layout.count():
            item = self.days_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Vider la liste des widgets jour et le dictionnaire des recettes utilisées
        self.jour_widgets = []
        self.recettes_utilisees = {}

        # Récupérer les données des repas pour la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)

        # Identifier les recettes utilisées dans cette semaine
        for jour in JOURS_SEMAINE:
            for repas in repas_semaine[jour]:
                if repas.get("repas_type_id"):
                    # Ajouter la recette au dictionnaire si elle n'y est pas déjà
                    self.recettes_utilisees[repas["repas_type_id"]] = True

        for col, jour in enumerate(JOURS_SEMAINE):
            # Créer un widget pour le jour
            day_widget = JourWidget(
                self.db_manager,
                jour,
                repas_semaine[jour],
                self.objectifs_utilisateur,
                self.semaine_id,
            )
            self.jour_widgets.append(day_widget)
            self.days_layout.addWidget(day_widget, 0, col)

        # Répartir les colonnes équitablement
        for col in range(len(JOURS_SEMAINE)):
            self.days_layout.setColumnStretch(col, 1)

        # Normaliser les ordres si nécessaire
        for jour in JOURS_SEMAINE:
            # Vérifier si des valeurs d'ordre sont fractionnaires
            has_fractional = False
            for repas in repas_semaine[jour]:
                if repas["ordre"] != int(repas["ordre"]):
                    has_fractional = True
                    break

            # Si des valeurs fractionnaires sont détectées, normaliser les ordres
            if has_fractional:
                self.db_manager.normaliser_ordres(jour, self.semaine_id)

    def print_planning(self):
        """Imprime le planning de la semaine actuelle"""
        self.print_manager.print_planning(self.semaine_id)

    def on_aliment_supprime(self):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir les données de cette semaine
        self.load_data()

    def on_repas_modifies(self, semaine_id):
        """Appelé lorsqu'un repas est modifié dans la semaine"""
        if semaine_id == self.semaine_id:
            self.load_data()

    # Dans SemaineWidget.on_recette_modifiee
    def on_recette_modifiee(self, recette_id):
        """Appelé lorsqu'une recette est modifiée"""
        # Vérifier si cette recette est utilisée dans cette semaine
        if recette_id in self.recettes_utilisees:
            # Mettre à jour tous les repas basés sur cette recette
            self.db_manager.update_repas_based_on_recipe(recette_id)
            self.load_data()

    def charger_objectifs_utilisateur(self):
        """Récupère les objectifs nutritionnels de l'utilisateur avec des valeurs par défaut sécuritaires"""
        try:
            user_data = self.db_manager.get_utilisateur()
            return {
                "calories": max(1, user_data.get("objectif_calories", 2500)),
                "proteines": max(1, user_data.get("objectif_proteines", 180)),
                "glucides": max(1, user_data.get("objectif_glucides", 250)),
                "lipides": max(1, user_data.get("objectif_lipides", 70)),
                "cout": 70,
            }
        except (KeyError, AttributeError, TypeError) as e:
            print(f"Erreur lors du chargement des objectifs utilisateur: {e}")
            # Retourner des valeurs par défaut en cas d'erreur
            return {
                "calories": 2500,
                "proteines": 180,
                "glucides": 250,
                "lipides": 70,
                "cout": 70,
            }

    def update_objectifs_utilisateur(self):
        """Met à jour les objectifs quand le profil utilisateur est modifié"""
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()
        for jour_widget in self.jour_widgets:
            jour_widget.update_objectifs(self.objectifs_utilisateur)
