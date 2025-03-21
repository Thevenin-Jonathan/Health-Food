from PySide6.QtWidgets import QPushButton


class RecentValueButton(QPushButton):
    """Bouton pour sélectionner une valeur récemment utilisée"""

    def __init__(self, text, value=None, parent=None, color_index=0):
        super().__init__(text, parent)
        self.value = value if value is not None else text

        # Définir la classe CSS et l'attribut de couleur
        self.setProperty("class", "quick-value-button")
        self.setProperty("colorType", str(color_index % 5))
