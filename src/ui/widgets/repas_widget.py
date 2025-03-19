from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QMessageBox,
)
from src.utils.config import BUTTON_STYLES
from src.ui.dialogs.aliment_repas_dialog import AlimentRepasDialog
from src.ui.dialogs.remplacer_repas_dialog import RemplacerRepasDialog


class RepasWidget(QFrame):
    """Widget représentant un repas dans le planning"""

    def __init__(self, db_manager, repas_data, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.repas_data = repas_data
        self.semaine_id = semaine_id

        # Configuration visuelle du cadre
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        repas_layout = QVBoxLayout(self)

        # Titre du repas avec boutons
        repas_header = QHBoxLayout()
        repas_title = QLabel(f"<h3>{self.repas_data['nom']}</h3>")
        repas_header.addWidget(repas_title)
        repas_header.addStretch()  # Ajouter un espace extensible pour pousser les boutons à droite

        # Bouton pour ajouter des aliments
        btn_add = QPushButton("+")
        btn_add.setFixedSize(24, 24)
        btn_add.setStyleSheet(BUTTON_STYLES["add"])
        btn_add.setToolTip("Ajouter un aliment à ce repas")
        btn_add.clicked.connect(self.add_food_to_meal)

        # Bouton pour remplacer le repas par une recette
        btn_replace = QPushButton("⇄")
        btn_replace.setFixedSize(24, 24)
        btn_replace.setStyleSheet(BUTTON_STYLES["replace"])
        btn_replace.setToolTip("Remplacer par une recette")
        btn_replace.clicked.connect(self.remplacer_repas_par_recette)

        # Bouton pour supprimer le repas
        btn_delete = QPushButton("×")
        btn_delete.setFixedSize(24, 24)
        btn_delete.setStyleSheet(BUTTON_STYLES["delete"])
        btn_delete.setToolTip("Supprimer ce repas")
        btn_delete.clicked.connect(self.delete_meal)

        # Ajouter les boutons au layout
        repas_header.addWidget(btn_add)
        repas_header.addWidget(btn_replace)
        repas_header.addWidget(btn_delete)
        repas_layout.addLayout(repas_header)

        # Ajouter les aliments du repas
        if self.repas_data["aliments"]:
            for aliment in self.repas_data["aliments"]:
                self.add_aliment_to_layout(aliment, repas_layout)
        else:
            repas_layout.addWidget(QLabel("Aucun aliment"))

        # Afficher les totaux du repas
        repas_layout.addWidget(
            QLabel(
                f"<b>Total:</b> {self.repas_data['total_calories']:.0f} kcal | "
                f"P: {self.repas_data['total_proteines']:.1f}g | "
                f"G: {self.repas_data['total_glucides']:.1f}g | "
                f"L: {self.repas_data['total_lipides']:.1f}g"
            )
        )

    def add_aliment_to_layout(self, aliment, parent_layout):
        """Ajoute un aliment au layout avec son bouton de suppression"""
        alim_layout = QHBoxLayout()

        # Texte de base de l'aliment
        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
        alim_label = QLabel(alim_text)
        alim_label.setWordWrap(True)
        alim_layout.addWidget(alim_label)
        alim_layout.addStretch()

        # Calculer les valeurs nutritionnelles
        calories = aliment["calories"] * aliment["quantite"] / 100
        proteines = aliment["proteines"] * aliment["quantite"] / 100
        glucides = aliment["glucides"] * aliment["quantite"] / 100
        lipides = aliment["lipides"] * aliment["quantite"] / 100

        # Créer un tooltip riche avec les informations détaillées
        tooltip_text = f"""<b>{aliment['nom']}</b> ({aliment['quantite']}g)<br>
                       <b>Calories:</b> {calories:.0f} kcal<br>
                       <b>Protéines:</b> {proteines:.1f}g<br>
                       <b>Glucides:</b> {glucides:.1f}g<br>
                       <b>Lipides:</b> {lipides:.1f}g"""

        if "fibres" in aliment and aliment["fibres"]:
            fibres = aliment["fibres"] * aliment["quantite"] / 100
            tooltip_text += f"<br><b>Fibres:</b> {fibres:.1f}g"

        alim_label.setToolTip(tooltip_text)

        # Bouton pour supprimer l'aliment
        btn_remove = QPushButton("×")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet(BUTTON_STYLES["delete"])
        btn_remove.setToolTip("Supprimer cet aliment")
        btn_remove.clicked.connect(lambda: self.remove_food_from_meal(aliment["id"]))
        alim_layout.addWidget(btn_remove)

        parent_layout.addLayout(alim_layout)

    def add_food_to_meal(self):
        """Ajouter un aliment au repas"""
        dialog = AlimentRepasDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()
            self.db_manager.ajouter_aliment_repas(
                self.repas_data["id"], aliment_id, quantite
            )
            self.update_parent_widget()

    def delete_meal(self):
        """Supprimer ce repas"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_repas(self.repas_data["id"])
            self.update_parent_widget()

    def remove_food_from_meal(self, aliment_id):
        """Supprimer un aliment du repas"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet aliment du repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_aliment_repas(self.repas_data["id"], aliment_id)
            self.update_parent_widget()

    def remplacer_repas_par_recette(self):
        """Remplace le repas par une recette"""
        dialog = RemplacerRepasDialog(self, self.db_manager, self.repas_data)
        if dialog.exec():
            recette_id, facteurs_ou_ingredients = dialog.get_data()

            # Supprimer l'ancien repas
            self.db_manager.supprimer_repas(self.repas_data["id"])

            if recette_id == "personnalisee":
                # Traiter le cas d'une recette personnalisée
                self.db_manager.appliquer_recette_modifiee_au_jour(
                    dialog.recette_courante_id,
                    facteurs_ou_ingredients,
                    self.repas_data["jour"],
                    self.repas_data["ordre"],
                    self.semaine_id,
                )
            else:
                # Appliquer une recette avec facteurs d'ajustement
                self.db_manager.appliquer_repas_type_au_jour_avec_facteurs(
                    recette_id,
                    self.repas_data["jour"],
                    self.repas_data["ordre"],
                    self.semaine_id,
                    facteurs_ou_ingredients,
                )

            self.update_parent_widget()

    def update_parent_widget(self):
        """Remonte jusqu'à la SemaineWidget et recharge les données"""
        parent = self.parent()
        while parent:
            if hasattr(parent, "load_data"):
                parent.load_data()
                break
            parent = parent.parent()
