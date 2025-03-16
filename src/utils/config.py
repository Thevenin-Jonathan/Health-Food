"""
Module de configuration pour l'application Health&Food
"""

# Constantes générales
APP_NAME = "Health & Food - Planificateur de Repas"
APP_VERSION = "1.0"

# Dimensions par défaut
DEFAULT_WINDOW_WIDTH = 1800
DEFAULT_WINDOW_HEIGHT = 1000

# Configuration de la base de données
DB_FILE = "nutrition_sportive.db"
DB_FOLDER = "data"

# Configuration de l'interface
JOURS_SEMAINE = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
]

# Styles CSS communs
BUTTON_STYLES = {
    "add": """
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
    """,
    "delete": """
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
    """,
    "replace": """
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
    """,
}
