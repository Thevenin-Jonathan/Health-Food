"""
Gestionnaire de thèmes pour l'application Health & Food
"""

from .qss_preprocessor import QSSPreprocessor

# Définition des thèmes disponibles
THEMES = {
    "Vert Nature": {
        "PRIMARY_COLOR": "#4CAF50",
        "PRIMARY_LIGHT": "#C8E6C9",
        "PRIMARY_DARK": "#388E3C",
        "ACCENT_COLOR": "#FF5722",
        "BACKGROUND_COLOR": "#f5f9f5",
        "TEXT_COLOR": "#2e3d32",
        "INPUT_TEXT_COLOR": "#2e3d32",
        "LIGHT_BG_COLOR": "#e0f0e0",
        "TAB_BG_COLOR": "#d4ead4",
        "TAB_HOVER_COLOR": "#9fd39f",
        "SELECTED_ITEM_BG": "#c6e5c6",
    },
    "Bleu Océan": {
        "PRIMARY_COLOR": "#2196F3",
        "PRIMARY_LIGHT": "#BBDEFB",
        "PRIMARY_DARK": "#1976D2",
        "ACCENT_COLOR": "#FF9800",
        "BACKGROUND_COLOR": "#f4f8fb",
        "TEXT_COLOR": "#263238",
        "INPUT_TEXT_COLOR": "#263238",
        "LIGHT_BG_COLOR": "#e3f2fd",
        "TAB_BG_COLOR": "#c6e2ff",
        "TAB_HOVER_COLOR": "#90caf9",
        "SELECTED_ITEM_BG": "#bbdefb",
    },
    "Violet Zen": {
        "PRIMARY_COLOR": "#9C27B0",
        "PRIMARY_LIGHT": "#E1BEE7",
        "PRIMARY_DARK": "#7B1FA2",
        "ACCENT_COLOR": "#FFC107",
        "BACKGROUND_COLOR": "#f8f5fa",
        "TEXT_COLOR": "#3e2347",
        "INPUT_TEXT_COLOR": "#3e2347",
        "LIGHT_BG_COLOR": "#f3e5f5",
        "TAB_BG_COLOR": "#e7d2eb",
        "TAB_HOVER_COLOR": "#d1c4e9",
        "SELECTED_ITEM_BG": "#e1bee7",
    },
    "Jour Ambre": {
        "PRIMARY_COLOR": "#FF9800",
        "PRIMARY_LIGHT": "#FFE0B2",
        "PRIMARY_DARK": "#F57C00",
        "ACCENT_COLOR": "#2196F3",
        "BACKGROUND_COLOR": "#fffaf0",
        "TEXT_COLOR": "#33291f",
        "INPUT_TEXT_COLOR": "#33291f",
        "LIGHT_BG_COLOR": "#fff3e0",
        "TAB_BG_COLOR": "#ffe0b2",
        "TAB_HOVER_COLOR": "#ffcc80",
        "SELECTED_ITEM_BG": "#ffecb3",
    },
    "Cerise": {
        "PRIMARY_COLOR": "#E91E63",
        "PRIMARY_LIGHT": "#F8BBD0",
        "PRIMARY_DARK": "#C2185B",
        "ACCENT_COLOR": "#00BCD4",
        "BACKGROUND_COLOR": "#fef5f8",
        "TEXT_COLOR": "#3b2c33",
        "INPUT_TEXT_COLOR": "#3b2c33",
        "LIGHT_BG_COLOR": "#fce4ec",
        "TAB_BG_COLOR": "#f8bbd0",
        "TAB_HOVER_COLOR": "#f48fb1",
        "SELECTED_ITEM_BG": "#f8bbd0",
    },
    "Mode Sombre": {
        "PRIMARY_COLOR": "#607D8B",
        "PRIMARY_LIGHT": "#B0BEC5",
        "PRIMARY_DARK": "#455A64",
        "ACCENT_COLOR": "#FF5722",
        "BACKGROUND_COLOR": "#263238",
        "TEXT_COLOR": "#eceff1",
        "INPUT_TEXT_COLOR": "#2e3d32",
        "LIGHT_BG_COLOR": "#37474f",
        "TAB_BG_COLOR": "#455a64",
        "TAB_HOVER_COLOR": "#546e7a",
        "SELECTED_ITEM_BG": "#78909c",
    },
}


class ThemeManager:
    """Gère les thèmes de l'application"""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.preprocessor = QSSPreprocessor()
        self.current_theme_name = "Vert Nature"  # Thème par défaut

        # Charger le thème depuis la base de données si disponible
        if db_manager:
            self.load_theme_from_db()

    def get_available_themes(self):
        """Retourne la liste des thèmes disponibles"""
        return list(THEMES.keys())

    def load_theme_from_db(self):
        """Charge le thème actif depuis la base de données"""
        user_data = self.db_manager.get_utilisateur()
        if user_data and "theme_actif" in user_data and user_data["theme_actif"]:
            theme_name = user_data["theme_actif"]
            if theme_name in THEMES:
                self.current_theme_name = theme_name
                return True
        return False

    def save_theme_to_db(self, theme_name):
        """Sauvegarde le thème actif dans la base de données"""
        if self.db_manager:
            # Récupérer les données utilisateur actuelles
            user_data = self.db_manager.get_utilisateur()
            if user_data:
                # Mettre à jour seulement la colonne theme_actif
                user_data["theme_actif"] = theme_name
                self.db_manager.sauvegarder_utilisateur(user_data)
                return True
        return False

    def apply_theme(self, theme_name):
        """Applique un thème spécifique"""
        if theme_name in THEMES:
            # Mettre à jour les variables du préprocesseur
            for key, value in THEMES[theme_name].items():
                self.preprocessor.add_variable(f"${key}", value)

            # Conserver le nom du thème actif
            self.current_theme_name = theme_name

            # Sauvegarder en base de données
            self.save_theme_to_db(theme_name)

            return True
        return False

    def get_current_theme(self):
        """Retourne le nom du thème actuel"""
        return self.current_theme_name

    def get_theme_colors(self, theme_name=None):
        """Retourne les couleurs du thème spécifié ou du thème actuel"""
        if not theme_name:
            theme_name = self.current_theme_name

        if theme_name in THEMES:
            return THEMES[theme_name]
        return None

    def generate_stylesheet(self, template_file, output_file=None):
        """Génère la feuille de style à partir du template avec le thème actuel"""
        # Réinitialiser les variables du préprocesseur pour éviter les conflits
        self.preprocessor = QSSPreprocessor()  # Cette ligne est importante !

        # Appliquer le thème actuel
        if self.current_theme_name in THEMES:
            for key, value in THEMES[self.current_theme_name].items():
                self.preprocessor.add_variable(f"${key}", value)

        # Générer le QSS
        return self.preprocessor.process(template_file, output_file)
