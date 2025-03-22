from PySide6.QtWidgets import QMainWindow, QTabWidget
from PySide6.QtCore import QTimer
from src.utils.events import EVENT_BUS
from .tabs.aliments_tab import AlimentsTab
from .tabs.planning_tab import PlanningTab
from .tabs.courses_tab import CoursesTab
from .tabs.recettes_tab import RecettesTab
from .tabs.utilisateur_tab import UtilisateurTab


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Nutrition Sportive - Planificateur de Repas")
        self.setMinimumSize(1280, 720)

        # Widget central avec onglets
        self.tabs = QTabWidget()

        # Connecter le changement d'onglet pour actualiser la liste des courses
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Onglet de planification des repas
        self.planning_tab = PlanningTab(self.db_manager)
        self.tabs.addTab(self.planning_tab, "Planning des repas")

        # Onglet de gestion des aliments
        self.aliments_tab = AlimentsTab(self.db_manager)
        self.tabs.addTab(self.aliments_tab, "Liste des aliments")

        # Onglet des recettes (repas types)
        self.recettes_tab = RecettesTab(self.db_manager)
        self.tabs.addTab(self.recettes_tab, "Mes repas")

        # Onglet de liste de courses
        self.courses_tab = CoursesTab(self.db_manager)
        self.tabs.addTab(self.courses_tab, "Liste de courses")

        # Onglet utilisateur avec calculs de calories
        self.utilisateur_tab = UtilisateurTab(self.db_manager)
        self.tabs.addTab(self.utilisateur_tab, "Utilisateur")

        # Définir comme widget central
        self.setCentralWidget(self.tabs)

        # Connexion aux signaux du PlanningTab pour la mise à jour des courses
        self.planning_tab.semaine_supprimee.connect(self.on_semaine_supprimee)
        self.planning_tab.semaine_ajoutee.connect(self.on_semaine_ajoutee)

        # Connexion aux signaux du bus d'événements (redondant mais pour sécurité)
        EVENT_BUS.semaine_ajoutee.connect(self.on_semaine_ajoutee)
        EVENT_BUS.semaine_supprimee.connect(self.on_semaine_supprimee)

    def on_tab_changed(self, index):
        """Appelé lorsque l'utilisateur change d'onglet"""
        # Si on passe à l'onglet des courses, actualiser la liste des semaines
        if index == 3:  # L'onglet des courses est le 4ème (index 3)
            QTimer.singleShot(50, self.courses_tab.charger_semaines)

    def on_semaine_supprimee(self):
        """Appelé lorsqu'une semaine est supprimée du planning"""

        # Mettre à jour la liste des courses
        if hasattr(self, "courses_tab"):
            QTimer.singleShot(
                50, self.courses_tab.charger_semaines
            )  # Léger délai pour assurer l'ordre d'exécution
        else:
            print("Erreur: courses_tab n'est pas accessible")

    def on_semaine_ajoutee(self):
        """Appelé lorsqu'une semaine est ajoutée au planning"""

        # Mettre à jour la liste des courses
        if hasattr(self, "courses_tab"):
            QTimer.singleShot(
                50, self.courses_tab.charger_semaines
            )  # Léger délai pour assurer l'ordre d'exécution
        else:
            print("Erreur: courses_tab n'est pas accessible")
