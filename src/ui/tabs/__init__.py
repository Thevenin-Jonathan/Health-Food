from .tab_base import TabBase
from .aliments_tab import AlimentsTab
from .planning_tab import PlanningTab
from .courses_tab import CoursesTab
from .recettes_tab import RecettesTab
from .utilisateur_tab import UtilisateurTab
from .options_tab import OptionsTab
from .aliments_composes_tab import AlimentsComposesTab

# Pour faciliter l'importation
__all__ = [
    "TabBase",
    "AlimentsTab",
    "AlimentsComposesTab",
    "PlanningTab",
    "CoursesTab",
    "RecettesTab",
    "UtilisateurTab",
    "OptionsTab",
]
