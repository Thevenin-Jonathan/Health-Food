from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)
from PySide6.QtCore import Qt


class TotauxMacrosWidget(QFrame):
    """Widget affichant les totaux nutritionnels avec barres de progression"""

    def __init__(
        self, total_cal, total_prot, total_gluc, total_lip, objectifs, compact=False
    ):
        super().__init__()
        self.total_cal = total_cal
        self.total_prot = total_prot
        self.total_gluc = total_gluc
        self.total_lip = total_lip
        self.objectifs = objectifs
        self.compact = compact

        # Configuration visuelle
        self.setFrameShape(QFrame.StyledPanel)
        self.setProperty("class", "day-total")

        # Appliquer un style plus compact si demandé
        if compact:
            self.setStyleSheet(
                """
                QFrame.day-total {
                    background-color: #f8f8f8;
                    border-radius: 4px;
                    padding: 5px;
                    margin-bottom: 4px;
                }
                QProgressBar {
                    max-height: 8px;
                    margin-top: 2px;
                    margin-bottom: 2px;
                }
                QLabel {
                    font-size: 10px;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QFrame.day-total {
                    background-color: #f8f8f8;
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 10px;
                }
            """
            )

        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        total_layout = QVBoxLayout(self)
        total_layout.setContentsMargins(
            8, 4 if self.compact else 8, 8, 4 if self.compact else 8
        )
        total_layout.setSpacing(2 if self.compact else 5)

        # Titre plus compact si demandé
        if self.compact:
            title = QLabel("<b>Total du jour</b>")
            title.setAlignment(Qt.AlignCenter)
            total_layout.addWidget(title)
        else:
            total_layout.addWidget(QLabel("<h3>Total du jour</h3>"))

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

    def add_macro_row(self, layout, label_text, value, target, unit=""):
        """Ajoute une ligne avec un label, une valeur et une barre de progression"""
        # En mode compact, utiliser une mise en page horizontale
        if self.compact:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)

            # Label - en mode compact est plus petit
            label = QLabel(f"{label_text}:")
            label.setFixedWidth(45)
            row_layout.addWidget(label)

            # Valeur - en mode compact, formaté "valeur/cible"
            value_label = QLabel(f"<b>{value:.0f}</b>/{target:.0f}{unit}")
            value_label.setFixedWidth(70)
            row_layout.addWidget(value_label)

            # Barre de progression plus fine
            progress = QProgressBar()
            progress.setMaximumHeight(6)  # Réduit la hauteur
            progress.setTextVisible(False)  # Pas de texte sur la barre
            progress.setRange(0, int(target * 1.4))  # Maximum à 140% de l'objectif
            progress.setValue(int(value))

            # Colorer la barre selon le pourcentage
            self._set_progress_bar_color(progress, value / target)

            row_layout.addWidget(progress, 1)  # Étirer la barre de progression

            layout.addLayout(row_layout)
        else:
            # Version non-compacte originale
            row_layout = QVBoxLayout()

            # En-tête avec label et valeur
            header_layout = QHBoxLayout()
            header_layout.addWidget(QLabel(f"<b>{label_text}</b>"))
            header_layout.addStretch()
            header_layout.addWidget(QLabel(f"{value:.0f} / {target:.0f} {unit}"))
            row_layout.addLayout(header_layout)

            # Barre de progression
            progress = QProgressBar()
            progress.setRange(0, int(target * 1.2))
            progress.setValue(int(value))

            # Colorer la barre selon le pourcentage
            self._set_progress_bar_color(progress, value / target)

            row_layout.addWidget(progress)
            layout.addLayout(row_layout)

    def _set_progress_bar_color(self, progress_bar, percentage):
        """Définit la couleur de la barre de progression en fonction du pourcentage"""
        # Cadre rouge - plus de 110%
        if percentage > 1.1:
            progress_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FF5252;  /* Rouge */
                }
                """
            )
        # Cadre jaune - entre 90% et 110%
        elif 0.9 <= percentage <= 1.1:
            progress_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;  /* Vert */
                }
                """
            )
        # Cadre orange - en dessous de 90%
        else:
            progress_bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FFC107;  /* Orange */
                }
                """
            )

    def update_values(self, total_cal, total_prot, total_gluc, total_lip, objectifs):
        """Met à jour les valeurs des totaux et les barres de progression"""
        self.total_cal = total_cal
        self.total_prot = total_prot
        self.total_gluc = total_gluc
        self.total_lip = total_lip
        self.objectifs = objectifs

        # Supprimer l'ancien contenu
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        # Réinitialiser l'interface
        self.setup_ui()
