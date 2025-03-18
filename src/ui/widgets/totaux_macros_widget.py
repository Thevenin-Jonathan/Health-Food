from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QProgressBar,
)
from PySide6.QtGui import QPalette, QColor


class TotauxMacrosWidget(QFrame):
    """Widget affichant les totaux nutritionnels avec barres de progression"""

    def __init__(self, total_cal, total_prot, total_gluc, total_lip, objectifs):
        super().__init__()
        self.total_cal = total_cal
        self.total_prot = total_prot
        self.total_gluc = total_gluc
        self.total_lip = total_lip
        self.objectifs = objectifs

        # Configuration visuelle
        self.setFrameShape(QFrame.StyledPanel)
        self.setProperty("class", "day-total")

        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        total_layout = QVBoxLayout(self)
        total_layout.addWidget(QLabel(f"<h3>Total du jour</h3>"))

        # Calories
        self.add_macro_row(
            total_layout, "Calories", self.total_cal, self.objectifs["calories"], ""
        )

        # Protéines
        self.add_macro_row(
            total_layout, "Protéines", self.total_prot, self.objectifs["proteines"], "g"
        )

        # Glucides
        self.add_macro_row(
            total_layout, "Glucides", self.total_gluc, self.objectifs["glucides"], "g"
        )

        # Lipides
        self.add_macro_row(
            total_layout, "Lipides", self.total_lip, self.objectifs["lipides"], "g"
        )

    def add_macro_row(self, parent_layout, name, value, target, unit):
        """Ajoute une ligne pour un macro-nutriment avec sa barre de progression"""
        # Layout pour cette ligne
        row_layout = QHBoxLayout()

        # Label avec nom et valeur
        value_label = QLabel(f"<b>{name}:</b> {value:.1f}{unit}")
        row_layout.addWidget(value_label)

        # Calculer le pourcentage de l'objectif
        pct = int((value / target) * 100) if target > 0 else 0
        obj_label = QLabel(f"/ {target}{unit} ({pct}%)")
        row_layout.addWidget(obj_label)

        # Ajouter le layout au parent
        parent_layout.addLayout(row_layout)

        # Créer et ajouter la barre de progression
        progress_bar = self.create_background_progress_bar(value, target)
        parent_layout.addWidget(progress_bar)

    def create_background_progress_bar(self, value, max_value):
        """Crée une barre de progression stylisée"""
        progress = QProgressBar()
        progress.setMinimum(0)

        # Pour l'affichage visuel de la barre
        if value > max_value:
            progress.setMaximum(int(value * 1.1))
        else:
            progress.setMaximum(max_value)

        progress.setValue(value)
        progress.setTextVisible(False)
        progress.setFixedHeight(10)

        # Coloration de la barre selon l'atteinte de l'objectif
        palette = QPalette()
        if value < max_value * 0.8:
            palette.setColor(QPalette.Highlight, QColor("orange"))  # En dessous
        elif value <= max_value * 1.05:
            palette.setColor(QPalette.Highlight, QColor("#4CAF50"))  # Dans la cible
        else:
            palette.setColor(QPalette.Highlight, QColor("#F44336"))  # Au-dessus

        progress.setPalette(palette)

        # Style CSS pour une apparence discrète
        progress.setStyleSheet(
            """
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                margin: 2px 0px;
            }
        """
        )

        return progress
