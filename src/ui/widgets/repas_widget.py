from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QMessageBox,
    QApplication,
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import Qt, QMimeData, QByteArray
from PySide6.QtGui import QDrag, QPainter, QPixmap
from src.ui.dialogs.aliment_repas_dialog import AlimentRepasDialog
from src.ui.dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from src.ui.dialogs.repas_edition_dialog import RepasEditionDialog
from src.utils.events import EVENT_BUS


class RepasWidget(QFrame):
    """Widget représentant un repas dans le planning"""

    def __init__(
        self, db_manager, repas_data, semaine_id, jour=None, compact_mode=True
    ):
        super().__init__()
        self.db_manager = db_manager
        self.repas_data = repas_data
        self.semaine_id = semaine_id
        self.jour = jour if jour else repas_data.get("jour", "")
        self.compact_mode = compact_mode
        self.is_expanded = False

        # Configuration pour drag and drop
        self.setMouseTracking(True)

        # Style visuel
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #E0E0E0;
                padding: 5px;
                margin: 3px 0px;
            }
            QFrame:hover {
                background-color: #F5F5F5;
                border: 1px solid #BDBDBD;
            }
            """
        )

        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        self.repas_layout = QVBoxLayout(self)
        self.repas_layout.setContentsMargins(10, 8, 10, 8)
        self.repas_layout.setSpacing(5)

        # En-tête du repas avec titre et boutons
        header_layout = QHBoxLayout()
        header_layout.setSpacing(3)

        # Bouton d'expansion
        self.expand_btn = QPushButton("▼" if not self.is_expanded else "▲")
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.setFixedSize(20, 20)
        self.expand_btn.clicked.connect(self.toggle_details)
        header_layout.addWidget(self.expand_btn)

        # Titre du repas
        titre_repas = QLabel(f"<b>{self.repas_data['nom']}</b>")
        header_layout.addWidget(titre_repas)

        # Calories (toujours visibles)
        calories_label = QLabel(f"{self.repas_data['total_calories']:.0f} kcal")
        calories_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        calories_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(calories_label, 1)  # 1 = stretch factor

        # Boutons d'actions (toujours visibles)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(2)

        # Bouton d'édition
        btn_edit = QPushButton("✐")
        btn_edit.setObjectName("editButton")
        btn_edit.setFixedSize(24, 24)
        btn_edit.setToolTip("Modifier ce repas")
        btn_edit.clicked.connect(self.edit_repas)
        buttons_layout.addWidget(btn_edit)

        # Bouton pour remplacer le repas par une recette
        btn_replace = QPushButton("⇄")
        btn_replace.setObjectName("replaceButton")
        btn_replace.setFixedSize(24, 24)
        btn_replace.setToolTip("Remplacer par une recette")
        btn_replace.clicked.connect(self.remplacer_repas_par_recette)
        buttons_layout.addWidget(btn_replace)

        # Bouton de suppression
        btn_delete = QPushButton("〤")
        btn_delete.setObjectName("deleteBigButton")
        btn_delete.setFixedSize(24, 24)
        btn_delete.setToolTip("Supprimer ce repas")
        btn_delete.clicked.connect(self.delete_repas)
        buttons_layout.addWidget(btn_delete)

        header_layout.addLayout(buttons_layout)
        self.repas_layout.addLayout(header_layout)

        # Zone détaillée (cachée initialement si mode compact)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(5, 5, 5, 0)
        self.details_layout.setSpacing(3)

        # Résumé des macros (visible même quand replié)
        self.macro_summary = QLabel(
            f"P: <b>{self.repas_data['total_proteines']:.1f}g</b> | "
            f"G: <b>{self.repas_data['total_glucides']:.1f}g</b> | "
            f"L: <b>{self.repas_data['total_lipides']:.1f}g</b>"
        )
        self.macro_summary.setAlignment(Qt.AlignCenter)
        self.repas_layout.addWidget(self.macro_summary)

        # Ajouter les aliments du repas dans la zone détaillée
        if self.repas_data["aliments"]:
            # Ajouter un bouton pour ajouter un aliment
            btn_add_food = QPushButton("+ Ajouter un aliment")
            btn_add_food.setObjectName("addFoodButton")
            btn_add_food.clicked.connect(self.add_food_to_meal)
            self.details_layout.addWidget(btn_add_food)

            for aliment in self.repas_data["aliments"]:
                self.add_aliment_to_layout(aliment, self.details_layout)
        else:
            empty_label = QLabel("Aucun aliment")
            empty_label.setAlignment(Qt.AlignCenter)
            self.details_layout.addWidget(empty_label)

            # Ajouter un bouton pour ajouter un aliment
            btn_add_food = QPushButton("+ Ajouter un aliment")
            btn_add_food.setObjectName("addFoodButton")
            btn_add_food.clicked.connect(self.add_food_to_meal)
            self.details_layout.addWidget(btn_add_food)

        # Ajouter la zone détaillée au layout principal
        self.repas_layout.addWidget(self.details_widget)

        # Cacher les détails en mode compact
        if self.compact_mode:
            self.details_widget.setVisible(False)

        # Assurer que les labels s'adaptent à la largeur
        for label in self.findChildren(QLabel):
            label.setWordWrap(True)

        # Définir une largeur minimale et une politique de taille
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def toggle_details(self):
        """Affiche ou masque les détails du repas"""
        self.is_expanded = not self.is_expanded
        self.details_widget.setVisible(self.is_expanded)

        # Changer l'icône du bouton
        self.expand_btn.setText("▲" if self.is_expanded else "▼")

        # Informer le container parent qu'il doit se réajuster
        if self.parent():
            self.parent().updateGeometry()

    def add_aliment_to_layout(self, aliment, parent_layout):
        """Ajoute un aliment au layout avec son bouton de suppression"""
        alim_layout = QHBoxLayout()
        alim_layout.setSpacing(2)  # Réduit l'espacement entre les éléments
        alim_layout.setContentsMargins(0, 0, 0, 0)  # Supprime les marges

        # Bouton pour supprimer l'aliment
        btn_remove = QPushButton("〤")
        btn_remove.setObjectName("deleteButton")
        btn_remove.setToolTip("Supprimer")
        btn_remove.clicked.connect(lambda: self.remove_food_from_meal(aliment["id"]))
        alim_layout.addWidget(btn_remove)

        # Texte de base de l'aliment
        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
        alim_label = QLabel(alim_text)
        # alim_label.setWordWrap(True)
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

    def edit_repas(self):
        """Ouvre la boîte de dialogue d'édition du repas"""
        dialog = RepasEditionDialog(self, self.db_manager, self.repas_data["id"])
        if dialog.exec():
            # Notifier que les repas ont été modifiés pour déclencher le rechargement
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

    def delete_repas(self):
        """Supprime le repas après confirmation"""
        confirm = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer le repas {self.repas_data['nom']} ?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            self.db_manager.supprimer_repas(self.repas_data["id"])
            # Notifier que les repas ont été modifiés
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

    def enterEvent(self, event):
        """Se déclenche quand la souris entre dans le widget"""
        # Changer le curseur en main ouverte pour indiquer qu'on peut faire un drag
        self.setCursor(Qt.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Se déclenche quand la souris quitte le widget"""
        # Restaurer le curseur par défaut
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Gère le clic de souris pour initier le drag and drop"""
        if event.button() == Qt.LeftButton:
            # Démarrer l'opération de drag
            self.setCursor(Qt.ClosedHandCursor)  # Changer le curseur en main fermée

            # Créer un drag
            drag = QDrag(self)
            mime_data = QMimeData()

            # Format des données: repas_id|jour
            data = QByteArray(f"{self.repas_data['id']}|{self.jour}".encode())
            mime_data.setData("application/x-repas", data)

            drag.setMimeData(mime_data)

            # Définir un feedback visuel (ici, une copie du widget)
            pixmap = self.grab()

            # Créer une nouvelle image transparente
            transparent_pixmap = QPixmap(pixmap.size())
            transparent_pixmap.fill(Qt.transparent)
            # Dessiner l'image originale avec transparence sur la nouvelle image
            painter = QPainter(transparent_pixmap)
            painter.setOpacity(0.7)  # 70% d'opacité (30% de transparence)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(transparent_pixmap)
            drag.setHotSpot(event.pos())

            # Exécuter le drag
            drag.exec(Qt.MoveAction)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Gère le relâchement du bouton de la souris"""
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.OpenHandCursor)
            QApplication.restoreOverrideCursor()
        super().mouseReleaseEvent(event)
