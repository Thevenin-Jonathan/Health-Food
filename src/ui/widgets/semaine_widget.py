from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QStyle,
)

from ...utils.events import event_bus
from ...utils.config import JOURS_SEMAINE
from .jour_widget import JourWidget
from .print_manager import PrintManager


class SemaineWidget(QWidget):
    """Widget représentant une semaine de planning"""

    def __init__(self, db_manager, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.semaine_id = semaine_id  # Identifiant numérique de la semaine
        self.print_manager = PrintManager(self.db_manager)

        # Charger les objectifs utilisateur dès l'initialisation
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()

        # Liste de widgets jour pour référence
        self.jour_widgets = []

        self.setup_ui()
        self.load_data()

        # S'abonner aux événements
        event_bus.aliment_supprime.connect(self.on_aliment_supprime)
        if hasattr(event_bus, "utilisateur_modifie"):
            event_bus.utilisateur_modifie.connect(self.update_objectifs_utilisateur)
        event_bus.repas_modifies.connect(self.on_repas_modifies)

    def charger_objectifs_utilisateur(self):
        """Récupère les objectifs nutritionnels de l'utilisateur"""
        user_data = self.db_manager.get_utilisateur()
        return {
            "calories": user_data.get("objectif_calories", 2500),
            "proteines": user_data.get("objectif_proteines", 180),
            "glucides": user_data.get("objectif_glucides", 250),
            "lipides": user_data.get("objectif_lipides", 70),
        }

    def update_objectifs_utilisateur(self):
        """Met à jour les objectifs quand le profil utilisateur est modifié"""
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Bouton pour imprimer le planning
        print_layout = QHBoxLayout()
        self.btn_print = QPushButton("Imprimer le planning")
        # Utiliser une icône standard disponible
        self.btn_print.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
        )
        self.btn_print.clicked.connect(self.print_planning)
        print_layout.addStretch()
        print_layout.addWidget(self.btn_print)
        main_layout.addLayout(print_layout)

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

        # Vider la liste des widgets jour
        self.jour_widgets = []

        # Récupérer les données des repas pour la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)

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

    def print_planning(self):
        """Imprime le planning de la semaine actuelle"""
        self.print_manager.print_planning(self.semaine_id)

    def on_aliment_supprime(self, aliment_id):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir les données de cette semaine
        self.load_data()

    def on_repas_modifies(self, semaine_id):
        """Appelé lorsqu'un repas est modifié dans la semaine"""
        if semaine_id == self.semaine_id:
            self.load_data()
