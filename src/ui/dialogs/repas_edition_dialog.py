from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt

from src.ui.dialogs.aliment_repas_dialog import AlimentRepasDialog
from src.utils.events import EVENT_BUS


class RepasEditionDialog(QDialog):
    """Dialogue pour éditer un repas existant"""

    def __init__(self, parent, db_manager, repas_id):
        super().__init__(parent)
        self.db_manager = db_manager
        self.repas_id = repas_id

        # Récupérer les données du repas
        self.repas_data = self._get_repas_data()

        # Configuration de la fenêtre
        self.setWindowTitle("Modifier le repas")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self.setup_ui()

    def _get_repas_data(self):
        """Récupérer les données complètes du repas"""
        # Utiliser la méthode directe pour récupérer le repas
        repas = self.db_manager.get_repas(self.repas_id)

        if repas:
            return repas

        # Si le repas n'est pas trouvé par la méthode directe, essayer avec les méthodes existantes
        aliments = self.db_manager.get_aliments_repas(self.repas_id)

        return {
            "id": self.repas_id,
            "nom": "Repas inconnu",
            "aliments": aliments,
            "total_calories": sum(
                a["calories"] * a["quantite"] / 100 for a in aliments
            ),
            "total_proteines": sum(
                a["proteines"] * a["quantite"] / 100 for a in aliments
            ),
            "total_glucides": sum(
                a["glucides"] * a["quantite"] / 100 for a in aliments
            ),
            "total_lipides": sum(a["lipides"] * a["quantite"] / 100 for a in aliments),
        }

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Champ pour le nom du repas
        nom_layout = QHBoxLayout()
        nom_layout.addWidget(QLabel("Nom du repas:"))
        self.nom_input = QLineEdit(self.repas_data["nom"])
        nom_layout.addWidget(self.nom_input)
        layout.addLayout(nom_layout)

        # Affichage des totaux nutritionnels
        totaux_frame = QFrame()
        totaux_frame.setFrameShape(QFrame.StyledPanel)
        totaux_frame.setStyleSheet(
            "background-color: #f0f0f0; border-radius: 5px; padding: 10px;"
        )
        totaux_layout = QVBoxLayout(totaux_frame)

        totaux_layout.addWidget(QLabel("<b>Valeurs nutritionnelles totales:</b>"))
        totaux_layout.addWidget(
            QLabel(f"Calories: {self.repas_data['total_calories']:.0f} kcal")
        )
        totaux_layout.addWidget(
            QLabel(f"Protéines: {self.repas_data['total_proteines']:.1f} g")
        )
        totaux_layout.addWidget(
            QLabel(f"Glucides: {self.repas_data['total_glucides']:.1f} g")
        )
        totaux_layout.addWidget(
            QLabel(f"Lipides: {self.repas_data['total_lipides']:.1f} g")
        )

        layout.addWidget(totaux_frame)

        # Liste des aliments
        layout.addWidget(QLabel("<b>Mes aliments:</b>"))

        self.aliments_list = QListWidget()
        self._populate_aliments_list()
        layout.addWidget(self.aliments_list)

        # Boutons pour gérer les aliments
        aliments_buttons_layout = QHBoxLayout()

        btn_add_aliment = QPushButton("Ajouter un aliment")
        btn_add_aliment.clicked.connect(self.add_aliment)
        aliments_buttons_layout.addWidget(btn_add_aliment)

        btn_remove_aliment = QPushButton("Supprimer l'aliment sélectionné")
        btn_remove_aliment.clicked.connect(self.remove_aliment)
        aliments_buttons_layout.addWidget(btn_remove_aliment)

        layout.addLayout(aliments_buttons_layout)

        # Boutons de validation/annulation
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("cancelButton")  # Ajout de l'ID pour le style
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("saveButton")  # Ajout de l'ID pour le style
        btn_save.clicked.connect(self.save_repas)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

        # Définir ce layout comme le layout principal
        self.setLayout(layout)

    def _populate_aliments_list(self):
        """Remplit la liste des aliments"""
        self.aliments_list.clear()
        for aliment in self.repas_data["aliments"]:
            item = QListWidgetItem(
                f"{aliment['nom']} ({aliment['quantite']}g) - "
                f"{aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
            )
            item.setData(Qt.UserRole, aliment)
            self.aliments_list.addItem(item)

    def add_aliment(self):
        """Ajoute un aliment au repas"""
        dialog = AlimentRepasDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()

            # Récupérer les détails de l'aliment
            aliment = self.db_manager.get_aliment(aliment_id)
            if aliment:
                aliment["quantite"] = quantite

                # Ajouter à la base de données
                self.db_manager.ajouter_aliment_repas(
                    self.repas_id, aliment_id, quantite
                )

                # Mettre à jour les totaux
                self.repas_data["total_calories"] += (
                    aliment["calories"] * quantite / 100
                )
                self.repas_data["total_proteines"] += (
                    aliment["proteines"] * quantite / 100
                )
                self.repas_data["total_glucides"] += (
                    aliment["glucides"] * quantite / 100
                )
                self.repas_data["total_lipides"] += aliment["lipides"] * quantite / 100

                # Ajouter à la liste des aliments
                self.repas_data["aliments"].append(aliment)

                # Mettre à jour l'affichage
                self._populate_aliments_list()

                # Notifier les changements
                EVENT_BUS.repas_modifies.emit(self.repas_data.get("semaine_id"))

    def remove_aliment(self):
        """Supprime l'aliment sélectionné"""
        current_item = self.aliments_list.currentItem()
        if current_item:
            aliment = current_item.data(Qt.UserRole)

            reply = QMessageBox.question(
                self,
                "Confirmer la suppression",
                f"Voulez-vous vraiment supprimer {aliment['nom']} du repas ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # Supprimer de la base de données
                self.db_manager.supprimer_aliment_repas(self.repas_id, aliment["id"])

                # Mettre à jour les totaux
                self.repas_data["total_calories"] -= (
                    aliment["calories"] * aliment["quantite"] / 100
                )
                self.repas_data["total_proteines"] -= (
                    aliment["proteines"] * aliment["quantite"] / 100
                )
                self.repas_data["total_glucides"] -= (
                    aliment["glucides"] * aliment["quantite"] / 100
                )
                self.repas_data["total_lipides"] -= (
                    aliment["lipides"] * aliment["quantite"] / 100
                )

                # Supprimer de la liste des aliments
                self.repas_data["aliments"] = [
                    a for a in self.repas_data["aliments"] if a["id"] != aliment["id"]
                ]

                # Mettre à jour l'affichage
                self._populate_aliments_list()

                # Notifier les changements
                EVENT_BUS.repas_modifies.emit(self.repas_data.get("semaine_id"))

    def save_repas(self):
        """Enregistre les modifications du repas"""
        # Mettre à jour le nom du repas si nécessaire
        nouveau_nom = self.nom_input.text().strip()
        if nouveau_nom and nouveau_nom != self.repas_data["nom"]:
            # Mettre à jour le nom dans la base de données
            self.db_manager.modifier_nom_repas(self.repas_id, nouveau_nom)

            # Notifier les changements
            EVENT_BUS.repas_modifies.emit(self.repas_data.get("semaine_id"))

        # Accepter le dialogue
        self.accept()
