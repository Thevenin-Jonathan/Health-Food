from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from ...utils.config import BUTTON_STYLES
from ..dialogs.repas_dialog import RepasDialog
from .repas_widget import RepasWidget
from .totaux_macros_widget import TotauxMacrosWidget
from ...utils.events import event_bus


class JourWidget(QWidget):
    """Widget représentant un jour de la semaine"""

    def __init__(self, db_manager, jour, repas_list, objectifs_utilisateur, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.jour = jour
        self.repas_list = repas_list
        self.objectifs_utilisateur = objectifs_utilisateur
        self.semaine_id = semaine_id

        self.setup_ui()

    def setup_ui(self):
        # Configuration du layout
        self.setMaximumWidth(350)
        self.layout = QVBoxLayout(self)

        # Titre du jour avec bouton d'ajout
        jour_header = QHBoxLayout()
        titre_jour = QLabel(f"<h2>{self.jour}</h2>")
        jour_header.addWidget(titre_jour)

        # Bouton pour ajouter un repas à ce jour
        btn_add_day = QPushButton("+")
        btn_add_day.setFixedSize(30, 30)
        btn_add_day.setStyleSheet(BUTTON_STYLES["add"])
        btn_add_day.setToolTip(f"Ajouter un repas le {self.jour}")
        btn_add_day.clicked.connect(self.add_meal)
        jour_header.addWidget(btn_add_day)

        self.layout.addLayout(jour_header)

        # Initialiser les totaux du jour
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0

        # Ajouter les repas du jour
        for repas in self.repas_list:
            repas_widget = RepasWidget(self.db_manager, repas, self.semaine_id)
            self.layout.addWidget(repas_widget)

            # Ajouter aux totaux du jour
            total_cal += repas["total_calories"]
            total_prot += repas["total_proteines"]
            total_gluc += repas["total_glucides"]
            total_lip += repas["total_lipides"]

        # Ajouter le widget des totaux
        totaux_widget = TotauxMacrosWidget(
            total_cal, total_prot, total_gluc, total_lip, self.objectifs_utilisateur
        )
        self.layout.addWidget(totaux_widget)

        # Ajouter un espacement extensible en bas
        self.layout.addStretch()

    def add_meal(self):
        """Ajoute un repas pour ce jour"""
        dialog = RepasDialog(
            self, self.db_manager, self.semaine_id, jour_predefini=self.jour
        )
        if dialog.exec():
            nom, jour, ordre, repas_type_id = dialog.get_data()

            if repas_type_id:
                # Utiliser une recette existante
                self.db_manager.appliquer_repas_type_au_jour(
                    repas_type_id, jour, ordre, self.semaine_id
                )
            else:
                # Créer un nouveau repas vide
                self.db_manager.ajouter_repas(nom, jour, ordre, self.semaine_id)

            # Émettre le signal pour notifier que les repas ont été modifiés
            event_bus.repas_modifies.emit(self.semaine_id)

            # Notifier le widget parent pour recharger les données
            parent = self.parent()
            if parent and hasattr(parent, "load_data"):
                parent.load_data()
