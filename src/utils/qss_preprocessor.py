"""
Préprocesseur QSS - Traite les fichiers QSS avec variables et fonctions
"""

import re
import os
import colorsys


class QSSPreprocessor:
    def __init__(self):
        """Initialise le préprocesseur avec des variables par défaut"""

        # Variables de base
        self.variables = {
            # Couleurs principales
            "$PRIMARY_COLOR": "#4CAF50",
            "$PRIMARY_LIGHT": "#C8E6C9",
            "$PRIMARY_DARK": "#388E3C",
            "$ACCENT_COLOR": "#FF5722",
            "$DANGER_COLOR": "#e74c3c",
            "$WARNING_COLOR": "#f39c12",
            "$INFO_COLOR": "#3498db",
            # Couleurs d'arrière-plan et de texte
            "$BACKGROUND_COLOR": "#f5f9f5",
            "$TEXT_COLOR": "#2e3d32",
            "$TEXT_HINT": "#666666",
            "$LIGHT_BG_COLOR": "#e0f0e0",
            # Couleurs spécifiques qui apparaissent dans votre CSS
            "$TAB_BG_COLOR": "#d4ead4",
            "$TAB_HOVER_COLOR": "#9fd39f",
            "$SELECTED_ITEM_BG": "#c6e5c6",
            # Dimensions
            "$BORDER_RADIUS": "4px",
            "$PADDING_SMALL": "4px",
            "$PADDING_MEDIUM": "6px 12px",
            "$PADDING_LARGE": "8px 16px",
        }

        # Fonctions disponibles
        self.functions = {
            "lighten": self._lighten,
            "darken": self._darken,
            "saturate": self._saturate,
            "desaturate": self._desaturate,
            "alpha": self._alpha,
        }

    def add_variable(self, name, value):
        """Ajoute une variable personnalisée"""
        if not name.startswith("$"):
            name = "$" + name
        self.variables[name] = value

    def _parse_function_call(self, match):
        """Analyse et exécute un appel de fonction dans le QSS"""
        func_name = match.group(1)
        args = [arg.strip() for arg in match.group(2).split(",")]

        if func_name in self.functions:
            return self.functions[func_name](*args)
        return match.group(
            0
        )  # Retourne la chaîne originale si la fonction n'existe pas

    def _hex_to_rgb(self, hex_color):
        """Convertit une couleur hexadécimale en RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        """Convertit RGB en couleur hexadécimale"""
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}"

    def _rgb_to_hsv(self, rgb):
        """Convertit RGB en HSV"""
        r, g, b = rgb
        return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    def _hsv_to_rgb(self, hsv):
        """Convertit HSV en RGB"""
        h, s, v = hsv
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (r * 255, g * 255, b * 255)

    def _lighten(self, color, amount="10%"):
        """Éclaircit une couleur du pourcentage spécifié"""
        if not color.startswith("#"):
            color = self._resolve_variable(color)

        amount = float(amount.rstrip("%")) / 100

        rgb = self._hex_to_rgb(color)
        hsv = self._rgb_to_hsv(rgb)
        hsv = (hsv[0], hsv[1], min(1.0, hsv[2] + amount))
        rgb = self._hsv_to_rgb(hsv)

        return self._rgb_to_hex(rgb)

    def _darken(self, color, amount="10%"):
        """Assombrit une couleur du pourcentage spécifié"""
        if not color.startswith("#"):
            color = self._resolve_variable(color)

        amount = float(amount.rstrip("%")) / 100

        rgb = self._hex_to_rgb(color)
        hsv = self._rgb_to_hsv(rgb)
        hsv = (hsv[0], hsv[1], max(0.0, hsv[2] - amount))
        rgb = self._hsv_to_rgb(hsv)

        return self._rgb_to_hex(rgb)

    def _saturate(self, color, amount="10%"):
        """Augmente la saturation d'une couleur"""
        if not color.startswith("#"):
            color = self._resolve_variable(color)

        amount = float(amount.rstrip("%")) / 100

        rgb = self._hex_to_rgb(color)
        hsv = self._rgb_to_hsv(rgb)
        hsv = (hsv[0], min(1.0, hsv[1] + amount), hsv[2])
        rgb = self._hsv_to_rgb(hsv)

        return self._rgb_to_hex(rgb)

    def _desaturate(self, color, amount="10%"):
        """Diminue la saturation d'une couleur"""
        if not color.startswith("#"):
            color = self._resolve_variable(color)

        amount = float(amount.rstrip("%")) / 100

        rgb = self._hex_to_rgb(color)
        hsv = self._rgb_to_hsv(rgb)
        hsv = (hsv[0], max(0.0, hsv[1] - amount), hsv[2])
        rgb = self._hsv_to_rgb(hsv)

        return self._rgb_to_hex(rgb)

    def _alpha(self, color, opacity="0.5"):
        """Ajoute de la transparence à une couleur (retourne rgba)"""
        if not color.startswith("#"):
            color = self._resolve_variable(color)

        rgb = self._hex_to_rgb(color)
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

    def _resolve_variable(self, var_name):
        """Résout une variable de style"""
        if not var_name.startswith("$"):
            var_name = "$" + var_name

        if var_name in self.variables:
            value = self.variables[var_name]
            # Vérifier si la valeur est elle-même une référence à une variable
            if isinstance(value, str) and value.startswith("$"):
                return self._resolve_variable(value)
            return value
        return var_name  # Retourne le nom de la variable si non trouvée

    def process(self, input_file, output_file=None):
        """
        Traite un fichier QSS avec des variables et génère le QSS final.
        """
        # Lire le fichier d'entrée
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Remplacer toutes les variables
        for var_name, var_value in self.variables.items():
            # Remplacer les variables au format $VAR_NAME
            content = content.replace(var_name, var_value)
            # Remplacer aussi les variables au format ${VAR_NAME}
            bracketed_var = "${" + var_name[1:] + "}"
            content = content.replace(bracketed_var, var_value)

        # Traiter les appels de fonction
        # Format: function_name(arg1, arg2, ...)
        function_pattern = r"([a-zA-Z_]+)\(([^)]+)\)"
        content = re.sub(function_pattern, self._parse_function_call, content)

        # Écrire le résultat dans un fichier ou le retourner
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

        return content


def process_qss(input_file, output_file=None):
    """Fonction utilitaire pour traiter un fichier QSS"""
    preprocessor = QSSPreprocessor()
    return preprocessor.process(input_file, output_file)
