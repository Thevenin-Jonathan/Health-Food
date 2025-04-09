from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QColorDialog,
    QFormLayout,
    QFrame,
)
from PySide6.QtGui import QColor


class CategorieDialog(QDialog):
    """Dialogue pour ajouter ou modifier une catégorie de repas"""

    def __init__(self, parent=None, categorie=None):
        super().__init__(parent)
        self.categorie = categorie
        self.couleur = categorie["couleur"] if categorie else "#3498db"
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(
            "Nouvelle catégorie" if not self.categorie else "Modifier la catégorie"
        )
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        # Nom de la catégorie
        self.nom_input = QLineEdit()
        if self.categorie:
            self.nom_input.setText(self.categorie["nom"])
        layout.addRow("Nom de la catégorie:", self.nom_input)

        # Couleur
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet(
            f"background-color: {self.couleur}; border: 1px solid #888;"
        )

        self.choose_color_btn = QPushButton("Choisir une couleur")
        self.choose_color_btn.clicked.connect(self.choose_color)

        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.choose_color_btn)

        layout.addRow("Couleur:", color_layout)

        # Boutons de confirmation
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.clicked.connect(self.validate_and_accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow("", buttons_layout)

    def choose_color(self):
        """Ouvre un sélecteur de couleur"""
        color = QColorDialog.getColor(QColor(self.couleur), self, "Choisir une couleur")
        if color.isValid():
            self.couleur = color.name()
            self.color_preview.setStyleSheet(
                f"background-color: {self.couleur}; border: 1px solid #888;"
            )

    def validate_and_accept(self):
        """Valide les données et accepte le dialogue"""
        if not self.nom_input.text().strip():
            # Afficher un message d'erreur
            return

        self.accept()

    def get_data(self):
        """Récupère les données saisies"""
        return {
            "nom": self.nom_input.text().strip(),
            "couleur": self.couleur,
        }
