"""
Package de widgets réutilisables pour l'interface utilisateur de Health-Food.
"""

# Exposer les classes principales pour faciliter l'importation
from .semaine_widget import SemaineWidget
from .jour_widget import JourWidget
from .repas_widget import RepasWidget
from .totaux_macros_widget import TotauxMacrosWidget
from .print_manager import PrintManager
from .nutrition_comparison import NutritionComparison
from .aliment_slider_widget import AlimentSliderWidget

# Cette configuration permet d'importer les widgets comme suit:
# from src.ui.widgets import SemaineWidget, JourWidget, RepasWidget
