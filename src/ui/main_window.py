from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from .tabs.aliments_tab import AlimentsTab
from .tabs.planning_tab import PlanningTab
from .tabs.courses_tab import CoursesTab
from .tabs.recettes_tab import RecettesTab  # Importer le nouvel onglet


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Nutrition Sportive - Planificateur de Repas")
        self.setMinimumSize(1800, 1000)

        # Widget central avec onglets
        self.tabs = QTabWidget()

        # Onglet de gestion des aliments
        self.aliments_tab = AlimentsTab(self.db_manager)
        self.tabs.addTab(self.aliments_tab, "Liste des aliments")

        # Onglet des recettes (repas types)
        self.recettes_tab = RecettesTab(self.db_manager)
        self.tabs.addTab(self.recettes_tab, "Recettes")

        # Onglet de planification des repas
        self.planning_tab = PlanningTab(self.db_manager)
        self.tabs.addTab(self.planning_tab, "Planning des repas")

        # Onglet de liste de courses
        self.courses_tab = CoursesTab(self.db_manager)
        self.tabs.addTab(self.courses_tab, "Liste de courses")

        # Définir comme widget central
        self.setCentralWidget(self.tabs)
