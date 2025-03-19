from PySide6.QtWidgets import QPushButton


class RecentValueButton(QPushButton):
    """Bouton pour sélectionner une valeur récemment utilisée"""

    def __init__(self, text, value=None, parent=None, color_index=0):
        super().__init__(text, parent)
        self.value = value if value is not None else text

        # Liste de couleurs pour les boutons récents
        colors = [
            "#4CAF50",  # Vert
            "#2196F3",  # Bleu
            "#FF9800",  # Orange
            "#9C27B0",  # Violet
            "#E91E63",  # Rose
        ]

        # Sélectionner une couleur en fonction de l'index
        color = colors[color_index % len(colors)]

        # Style avec couleur de fond distincte
        self.setStyleSheet(
            f"""
            QPushButton {{
                padding: 4px 8px;
                background-color: {color};
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}99;  /* Ajout d'une transparence au survol */
            }}
        """
        )
