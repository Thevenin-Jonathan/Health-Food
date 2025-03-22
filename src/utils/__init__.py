"""
Utilitaires pour l'application Health&Food
Ce module centralise les fonctions et classes utilitaires utilisées dans l'application.
"""

# Importation des utilitaires de texte
from .text_utils import normalize_str

# Importation des configurations
from .config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DB_FILE,
    DB_FOLDER,
    JOURS_SEMAINE,
)

# Importation des utilitaires d'interface utilisateur
from .ui_helpers import (
    DialogAutoSelectFilter,
    ButtonCursorHandler,
    AutoSelectTextEdit,
    AutoSelectSpinBox,
    AutoSelectDoubleSpinBox,
    LineEditSelectAllFilter,
    apply_auto_select_to_widget,
)

# Importation du système d'événements
from .events import EVENT_BUS

# Définir ce qui est exposé lors de l'utilisation de "from src.utils import *"
__all__ = [
    # Text Utils
    "normalize_str",
    # Config
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_WINDOW_WIDTH",
    "DEFAULT_WINDOW_HEIGHT",
    "DB_FILE",
    "DB_FOLDER",
    "JOURS_SEMAINE",
    # UI Helpers
    "DialogAutoSelectFilter",
    "ButtonCursorHandler",
    "AutoSelectTextEdit",
    "AutoSelectSpinBox",
    "AutoSelectDoubleSpinBox",
    "LineEditSelectAllFilter",
    "apply_auto_select_to_widget",
    # Events
    "EVENT_BUS",
]
