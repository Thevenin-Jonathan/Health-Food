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
    QScrollArea,
    QLineEdit,
    QInputDialog,
)
from PySide6.QtCore import Qt, QMimeData, QByteArray, Signal
from PySide6.QtGui import QDrag, QPainter, QPixmap
from src.ui.dialogs.aliment_repas_dialog import AlimentRepasDialog
from src.ui.dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from src.ui.dialogs.repas_edition_dialog import RepasEditionDialog
from src.utils.events import EVENT_BUS


class EditableTitleLabel(QLabel):
    """Label avec édition directe par double-clic"""

    titleChanged = Signal(str)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(
            Qt.PointingHandCursor
        )  # Curseur main pour indiquer qu'on peut cliquer

    def mouseDoubleClickEvent(self, event):
        """Gérer le double-clic pour éditer le titre"""
        # Extraire le texte actuel (enlever les balises HTML)
        current_text = self.text().replace("<b>", "").replace("</b>", "")

        # Demander le nouveau titre avec QInputDialog
        new_title, ok = QInputDialog.getText(
            self,
            "Modifier le titre",
            "Nouveau titre du repas:",
            QLineEdit.Normal,
            current_text,
        )

        if ok and new_title:
            # Mettre à jour le texte avec le format en gras
            self.setText(f"<b>{new_title}</b>")
            # Émettre le signal avec le nouveau titre
            self.titleChanged.emit(new_title)


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
        self.setProperty("class", "repas-widget")

        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        self.repas_layout = QVBoxLayout(self)
        self.repas_layout.setContentsMargins(8, 6, 8, 6)
        self.repas_layout.setSpacing(5)

        # ===== LIGNE 1: CALORIES (GAUCHE) ET BOUTONS (DROITE) =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(3)

        # Calories (à gauche)
        calories_label = QLabel(f"{self.repas_data['total_calories']:.0f} kcal")
        calories_label.setProperty("class", "calories-label")
        calories_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(calories_label)

        # Espace flexible entre les calories et les boutons
        header_layout.addStretch(1)

        # Boutons d'actions (à droite)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(2)

        # Bouton pour remplacer le repas par une recette
        btn_replace = QPushButton("⇄")
        btn_replace.setObjectName("replaceButton")
        btn_replace.setFixedSize(24, 24)
        btn_replace.setToolTip("Remplacer un repas")
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

        # ===== LIGNE 2: NOM DU REPAS (ÉDITABLE PAR DOUBLE-CLIC) =====
        # Créer un QLabel spécial pour le titre qui va gérer le double-clic
        self.titre_repas = EditableTitleLabel(f"<b>{self.repas_data['nom']}</b>", self)
        self.titre_repas.setAlignment(Qt.AlignLeft)
        self.titre_repas.setProperty("class", "repas-title")
        self.titre_repas.setToolTip("Double-cliquez pour modifier le titre")
        self.titre_repas.titleChanged.connect(self.update_repas_title)
        self.repas_layout.addWidget(self.titre_repas)

        # ===== LIGNE 3: RÉSUMÉ DES MACROS =====
        self.macro_summary = QLabel(
            f"<b>P:</b> {self.repas_data['total_proteines']:.1f}g | "
            f"<b>G:</b> {self.repas_data['total_glucides']:.1f}g | "
            f"<b>L:</b> {self.repas_data['total_lipides']:.1f}g"
        )
        self.macro_summary.setProperty("class", "macro-summary")
        self.macro_summary.setAlignment(Qt.AlignCenter)
        self.repas_layout.addWidget(self.macro_summary)

        # ===== LIGNE 4: DÉTAILS (INITIALEMENT MASQUÉS) =====
        # Zone détaillée (cachée initialement si mode compact)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(5, 5, 5, 0)
        self.details_layout.setSpacing(3)

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

        # ===== LIGNE 5: BOUTON D'EXPANSION (EN BAS) =====
        expand_container = QHBoxLayout()
        expand_container.setAlignment(Qt.AlignCenter)

        self.expand_btn = QPushButton("▼")
        self.expand_btn.setObjectName("expandButton")
        self.expand_btn.clicked.connect(self.toggle_details)
        expand_container.addWidget(self.expand_btn)

        self.repas_layout.addLayout(expand_container)

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

        # Changer l'icône du bouton selon l'état
        self.expand_btn.setText("▲" if self.is_expanded else "▼")

        # Ajuster la position du bouton pour qu'il ressemble à un onglet
        if self.is_expanded:
            self.expand_btn.setStyleSheet(
                """
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            """
            )
        else:
            self.expand_btn.setStyleSheet("")  # Revenir au style par défaut

        # Informer le container parent qu'il doit se réajuster
        if self.parent():
            self.parent().updateGeometry()

    def update_repas_title(self, new_title):
        """Met à jour le titre du repas dans la base de données"""
        # Mettre à jour la base de données
        self.db_manager.modifier_nom_repas(self.repas_data["id"], new_title)

        # Mettre à jour les données locales
        self.repas_data["nom"] = new_title

        # Notifier le changement
        EVENT_BUS.repas_modifies.emit(self.semaine_id)

    def add_aliment_to_layout(self, aliment, parent_layout):
        """Ajoute un aliment au layout avec son bouton de suppression"""
        # Créer un widget conteneur pour l'aliment
        alim_container = QWidget()
        alim_layout = QHBoxLayout(alim_container)
        alim_layout.setSpacing(2)  # Réduit l'espacement entre les éléments
        alim_layout.setContentsMargins(0, 0, 0, 0)  # Supprime les marges

        # Bouton pour supprimer l'aliment
        btn_remove = QPushButton("×")  # Symbole plus simple
        btn_remove.setObjectName("deleteButton")
        btn_remove.setFixedSize(18, 18)  # Taille réduite
        btn_remove.setToolTip("Supprimer")
        btn_remove.clicked.connect(lambda: self.remove_food_from_meal(aliment["id"]))
        alim_layout.addWidget(btn_remove)

        # Texte de base de l'aliment
        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
        alim_label = QLabel(alim_text)
        alim_label.setProperty("class", "aliment-item")
        alim_label.setWordWrap(True)
        alim_layout.addWidget(alim_label)
        alim_layout.addStretch()

        # Calculer les valeurs nutritionnelles pour le tooltip
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

        # Ajouter le widget conteneur au layout parent
        parent_layout.addWidget(alim_container)

    def add_food_to_meal(self):
        """Ajouter un aliment au repas"""
        dialog = AlimentRepasDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()
            self.db_manager.ajouter_aliment_repas(
                self.repas_data["id"], aliment_id, quantite
            )

            # Récupérer les données mises à jour
            repas_updated = self.db_manager.get_repas(self.repas_data["id"])
            if repas_updated:
                # Conserver l'état d'expansion
                was_expanded = self.is_expanded

                # Mettre à jour les données
                self.repas_data = repas_updated

                # Reconstruire l'interface
                self.clear_and_rebuild_details()
                self.update_summaries()

                # Restaurer l'état d'expansion
                if was_expanded:
                    self.is_expanded = True
                    self.details_widget.setVisible(True)
                    self.expand_btn.setText("▲")
                    self.expand_btn.setStyleSheet(
                        """
                        border-top-left-radius: 0px;
                        border-top-right-radius: 0px;
                        border-bottom-left-radius: 12px;
                        border-bottom-right-radius: 12px;
                    """
                    )

                # Mettre à jour les totaux du jour parent
                self.notify_parent_day_widget()

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
            # Supprimer l'aliment de la base de données
            self.db_manager.supprimer_aliment_repas(self.repas_data["id"], aliment_id)

            # Récupérer les données mises à jour du repas
            repas_updated = self.db_manager.get_repas(self.repas_data["id"])
            if repas_updated:
                # Conserver l'état d'expansion
                was_expanded = self.is_expanded

                # Mettre à jour les données locales
                self.repas_data = repas_updated

                # Reconstruire l'interface du repas sans recharger tout le contenu
                self.clear_and_rebuild_details()
                self.update_summaries()

                # Restaurer l'état d'expansion
                if was_expanded:
                    self.is_expanded = True
                    self.details_widget.setVisible(True)
                    self.expand_btn.setText("▲")
                    self.expand_btn.setStyleSheet(
                        """
                        border-top-left-radius: 0px;
                        border-top-right-radius: 0px;
                        border-bottom-left-radius: 12px;
                        border-bottom-right-radius: 12px;
                    """
                    )

                # Mettre à jour les totaux du jour parent sans tout recharger
                self.notify_parent_day_widget()

    def clear_and_rebuild_details(self):
        """Efface et reconstruit la section des détails du repas"""
        # Vider les détails existants
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Nettoyer les layouts imbriqués
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

        # Ajouter les aliments du repas dans la zone détaillée
        if self.repas_data["aliments"]:
            # Ajouter un bouton pour ajouter un aliment
            btn_add_food = QPushButton("+ Ajouter un aliment")
            btn_add_food.setObjectName("addFoodButton")
            btn_add_food.clicked.connect(self.add_food_to_meal)
            self.details_layout.addWidget(btn_add_food)

            # Créer un conteneur de défilement pour les aliments (scroll area)
            if len(self.repas_data["aliments"]) > 5:
                aliments_scroll = QScrollArea()
                aliments_scroll.setWidgetResizable(True)
                aliments_scroll.setFrameShape(QFrame.NoFrame)
                aliments_scroll.setMaximumHeight(150)  # Hauteur maximale

                aliments_container = QWidget()
                aliments_layout = QVBoxLayout(aliments_container)
                aliments_layout.setContentsMargins(0, 0, 0, 0)
                aliments_layout.setSpacing(3)

                # Ajouter les aliments au conteneur
                for aliment in self.repas_data["aliments"]:
                    self.add_aliment_to_layout(aliment, aliments_layout)

                aliments_scroll.setWidget(aliments_container)
                self.details_layout.addWidget(aliments_scroll)
            else:
                # Si peu d'aliments, les ajouter directement
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

    def update_summaries(self):
        """Met à jour les résumés nutritionnels"""
        # Mettre à jour les calories
        for i in range(self.repas_layout.count()):
            layout_item = self.repas_layout.itemAt(i)
            if isinstance(layout_item, QHBoxLayout):
                for j in range(layout_item.count()):
                    item = layout_item.itemAt(j)
                    if (
                        item.widget()
                        and isinstance(item.widget(), QLabel)
                        and hasattr(item.widget(), "property")
                    ):
                        label = item.widget()
                        if label.property("class") == "calories-label":
                            label.setText(
                                f"{self.repas_data['total_calories']:.0f} kcal"
                            )
                            break

        # Mettre à jour les macronutriments
        self.macro_summary.setText(
            f"<b>P:</b> {self.repas_data['total_proteines']:.1f}g | "
            f"<b>G:</b> {self.repas_data['total_glucides']:.1f}g | "
            f"<b>L:</b> {self.repas_data['total_lipides']:.1f}g"
        )

    def notify_parent_day_widget(self):
        """Notifie le widget jour parent pour mettre à jour ses totaux sans tout recharger"""
        # Trouver le widget jour parent
        parent = self.parent()
        while parent:
            if hasattr(parent, "update_day_totals"):
                parent.update_day_totals()
                break
            parent = parent.parent()

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
