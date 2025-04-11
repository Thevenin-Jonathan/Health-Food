import traceback
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
    QLineEdit,
    QInputDialog,
    QDialog,
    QRadioButton,
    QSpinBox,
    QDialogButtonBox,
    QButtonGroup,
)
from PySide6.QtCore import (
    Qt,
    QMimeData,
    QByteArray,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
)
from PySide6.QtGui import QDrag, QPixmap, QPainter
from src.ui.dialogs.aliment_repas_dialog import AlimentRepasDialog
from src.ui.dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from src.ui.dialogs.repas_edition_dialog import RepasEditionDialog
from src.ui.dialogs.correction_nutrition_dialog import CorrectionNutritionDialog
from src.utils.events import EVENT_BUS


class EditableAlimentLabel(QLabel):
    """Label d'aliment avec édition du poids par double-clic"""

    weightChanged = Signal(int, int)  # (aliment_id, nouvelle_quantité)

    def __init__(self, text, aliment_id, quantite_actuelle, parent=None):
        super().__init__(text, parent)
        self.aliment_id = aliment_id
        self.quantite_actuelle = quantite_actuelle
        self.setCursor(
            Qt.PointingHandCursor
        )  # Curseur main pour indiquer qu'on peut cliquer
        self.setToolTip("Double-cliquez pour modifier la quantité")

    def mouseDoubleClickEvent(self, _):  # pylint: disable=invalid-name
        """Gérer le double-clic pour éditer la quantité"""
        # Demander la nouvelle quantité avec QInputDialog
        new_quantity, ok = QInputDialog.getInt(
            self,
            "Modifier la quantité",
            "Nouvelle quantité (en grammes):",
            self.quantite_actuelle,  # Valeur par défaut
            1,  # Minimum
            5000,  # Maximum
            1,  # Pas
        )

        if ok and new_quantity != self.quantite_actuelle:
            # Émettre le signal avec l'ID de l'aliment et la nouvelle quantité
            self.weightChanged.emit(self.aliment_id, new_quantity)


class EditableTitleLabel(QLabel):
    """Label avec édition directe par double-clic"""

    titleChanged = Signal(str)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(
            Qt.PointingHandCursor
        )  # Curseur main pour indiquer qu'on peut cliquer

    def mouseDoubleClickEvent(self, _):  # pylint: disable=invalid-name
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
        self.multi_spin = QSpinBox()
        self.is_expanded = False
        self.drag_start_position = None
        self.drag_threshold = 10
        self.is_dragging = False
        self.animation = None

        # Initialiser les attributs qui sont définis plus tard dans le code
        self.repas_layout = None
        self.titre_repas = None
        self.macro_summary = None
        self.details_widget = None
        self.details_layout = None
        self.expand_btn = None
        self.btn_multi = None
        self._drag_object = None
        self._mime_data = None
        self._pixmap = None

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

        # Vérifier la cohérence des calories
        calories_affiches = self.repas_data["total_calories"]
        calories_calcules = (
            self.repas_data["total_proteines"] * 4
            + self.repas_data["total_glucides"] * 4
            + self.repas_data["total_lipides"] * 9
        )

        # Calculer l'écart en pourcentage
        if calories_calcules > 0:  # Éviter la division par zéro
            ecart_pct = (
                abs(calories_affiches - calories_calcules) / calories_calcules * 100
            )
        else:
            ecart_pct = 0

        # Créer le layout pour le bloc calories et alerte
        calories_alert_layout = QHBoxLayout()
        calories_alert_layout.setSpacing(2)
        calories_alert_layout.setContentsMargins(0, 0, 0, 0)

        # Calories (à gauche)
        calories_label = QLabel(f"{calories_affiches:.0f} kcal")
        calories_label.setProperty("class", "calories-label")
        calories_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        calories_alert_layout.addWidget(calories_label)

        # Ajouter une icône d'alerte si l'écart est trop important
        if ecart_pct > 5:
            alert_icon = QLabel("⚠️")
            alert_icon.setProperty("warning-icon", True)

            # Créer un tooltip détaillé
            diff = calories_affiches - calories_calcules
            signe = "+" if diff > 0 else ""
            tooltip = (
                f"<b>Attention</b>: Incohérence calorique détectée<br>"
                f"Calories affichées: <b>{calories_affiches:.0f} kcal</b><br>"
                f"Calories des macros: <b>{calories_calcules:.0f} kcal</b><br>"
                f"Différence: <b>{signe}{diff:.0f} kcal</b> ({ecart_pct:.1f}%)<br><br>"
                f"Cela peut indiquer une erreur dans les valeurs nutritionnelles des aliments."
            )
            alert_icon.setToolTip(tooltip)
            calories_alert_layout.addWidget(alert_icon)

        # Ajouter le layout des calories à l'en-tête
        header_layout.addLayout(calories_alert_layout)

        # Espace flexible entre les calories et les boutons
        header_layout.addStretch(1)

        # Obtenir l'info de multiplicateur pour ce repas
        repas_multi_info = self.db_manager.get_repas_multiplicateur(
            self.repas_data["id"]
        )
        multiplicateur = repas_multi_info.get("multiplicateur", 1)
        ignore_course = repas_multi_info.get("ignore_course", False)

        # Créer le bouton de multiplicateur
        self.btn_multi = QPushButton()
        self.btn_multi.setObjectName("multiButton")

        # Définir le texte et le style du bouton en fonction des paramètres
        if ignore_course:
            self.btn_multi.setText("Préparé")
            self.btn_multi.setProperty("status", "prepared")
            self.btn_multi.setToolTip(
                "Déjà préparé - n'apparaît pas dans la liste de courses"
            )
        else:
            self.btn_multi.setText(f"×{multiplicateur}")
            if multiplicateur > 1:
                self.btn_multi.setProperty("status", "multiplied")
                self.btn_multi.setToolTip(
                    f"Quantités multipliées par {multiplicateur} dans la liste de courses"
                )
            else:
                self.btn_multi.setProperty("status", "normal")
                self.btn_multi.setToolTip(
                    "Cliquez pour modifier la quantité dans la liste de courses"
                )

        # Connecter le clic du bouton
        self.btn_multi.clicked.connect(self.modifier_multiplicateur)
        header_layout.addWidget(self.btn_multi)

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

        self.expand_btn = QPushButton("▼/▲")
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
        """Affiche ou masque les détails du repas avec une animation"""
        is_visible = self.details_widget.isVisible()

        # Créer l'animation pour une transition fluide
        # Vérifier si l'animation existe et est en cours d'exécution
        if (
            self.animation is not None
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        # L'animation doit utiliser maximumHeight pour éviter les problèmes de layout
        self.animation = QPropertyAnimation(self.details_widget, b"maximumHeight")
        self.animation.setDuration(150)  # 150ms - rapide mais visible
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # Obtenir la hauteur cible avant de commencer l'animation
        target_height = self.details_widget.sizeHint().height()

        if is_visible:
            # Animation de fermeture - IMPORTANT: maintenir la visibilité pendant l'animation
            self.animation.setStartValue(self.details_widget.height())
            self.animation.setEndValue(0)

            # Uniquement masquer après la fin de l'animation
            self.animation.finished.connect(self._finish_closing_animation)

            # Ajuster le style du bouton pour qu'il ressemble à un onglet
            self.expand_btn.setStyleSheet("")  # Revenir au style par défaut
        else:
            # Animation d'ouverture - définir la hauteur maximale à 0 avant de rendre visible
            self.details_widget.setMaximumHeight(0)
            self.details_widget.setVisible(True)

            # S'assurer que le widget a une hauteur préférée correcte
            self.details_widget.adjustSize()

            # Commencer l'animation
            self.animation.setStartValue(0)
            self.animation.setEndValue(target_height)

            # Ajuster le style du bouton
            self.expand_btn.setStyleSheet(
                """
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                """
            )

            # Mettre à jour l'état d'expansion
            self.is_expanded = True

        # Connecter une fonction pour ajuster le layout pendant l'animation
        self.animation.valueChanged.connect(self._on_animation_update)
        self.animation.start()

    def _finish_closing_animation(self):
        """Finalise l'animation de fermeture des détails"""
        self.details_widget.setVisible(False)
        self.is_expanded = False

        # Informer le parent qu'il doit mettre à jour sa géométrie
        if self.parent():
            self.parent().updateGeometry()

    def _on_animation_update(self, _):
        """Appelé pendant l'animation pour s'assurer que le layout reste stable"""
        # Forcer la mise à jour du layout pour éviter les sauts
        self.repas_layout.activate()

        # Mettre à jour le conteneur parent
        if self.parent():
            self.parent().update()

    def update_repas_title(self, new_title):
        """Met à jour le titre du repas dans la base de données"""
        # Mettre à jour la base de données
        self.db_manager.modifier_nom_repas(self.repas_data["id"], new_title)

        # Mettre à jour les données locales
        self.repas_data["nom"] = new_title

        # Notifier le changement
        EVENT_BUS.repas_modifies.emit(self.semaine_id)

    def add_aliment_to_layout(self, aliment, parent_layout):
        """Ajoute un aliment au layout avec son bouton de suppression et alertes éventuelles"""
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

        # Calculer les valeurs nutritionnelles et le texte
        calories = aliment["calories"] * aliment["quantite"] / 100
        proteines = aliment["proteines"] * aliment["quantite"] / 100
        glucides = aliment["glucides"] * aliment["quantite"] / 100
        lipides = aliment["lipides"] * aliment["quantite"] / 100

        # Vérification de la cohérence des calories de l'aliment
        calories_calculees = (proteines * 4) + (glucides * 4) + (lipides * 9)

        # Calculer l'écart en pourcentage
        if calories_calculees > 0:  # Éviter la division par zéro
            ecart_pct = abs(calories - calories_calculees) / calories_calculees * 100
        else:
            ecart_pct = 0

        # Texte de base de l'aliment
        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {calories:.0f} kcal"

        # Utiliser notre nouveau label éditable
        alim_label = EditableAlimentLabel(
            alim_text, aliment["id"], aliment["quantite"], self
        )
        alim_label.setProperty("class", "aliment-item")
        alim_label.setWordWrap(True)
        alim_label.weightChanged.connect(self.update_aliment_weight)
        alim_layout.addWidget(alim_label)

        # Ajouter une icône d'alerte si l'écart est trop important (>5%)
        if ecart_pct > 5:
            alert_icon = QLabel("⚠️")
            alert_icon.setProperty("warning-icon", True)
            alert_icon.setProperty("size", "small")

            # Créer un tooltip détaillé pour l'aliment
            diff = calories - calories_calculees
            signe = "+" if diff > 0 else ""
            tooltip = (
                f"<b>Attention</b>: Incohérence calorique dans l'aliment '{aliment['nom']}'<br>"
                f"Calories indiquées: <b>{calories:.0f} kcal</b><br>"
                f"Calories calculées: <b>{calories_calculees:.0f} kcal</b><br>"
                f"Différence: <b>{signe}{diff:.0f} kcal</b> ({ecart_pct:.1f}%)<br><br>"
                f"Les valeurs nutritionnelles de cet aliment semblent incorrectes."
            )
            alert_icon.setToolTip(tooltip)
            current_aliment = aliment.copy()
            alert_icon.mousePressEvent = lambda event, a=current_aliment: self.correct_aliment_nutritional_values(
                a
            )
            alim_layout.addWidget(alert_icon)

        alim_layout.addStretch()

        # Créer un tooltip riche avec les informations détaillées
        tooltip_text = f"""<b>{aliment['nom']}</b> ({aliment['quantite']}g)<br>
                    <b>Calories:</b> {calories:.0f} kcal<br>
                    <b>Protéines:</b> {proteines:.1f}g<br>
                    <b>Glucides:</b> {glucides:.1f}g<br>
                    <b>Lipides:</b> {lipides:.1f}g"""

        if "fibres" in aliment and aliment["fibres"]:
            fibres = aliment["fibres"] * aliment["quantite"] / 100
            tooltip_text += f"<br><b>Fibres:</b> {fibres:.1f}g"

        # Ajouter une note sur l'incohérence dans le tooltip de l'aliment si nécessaire
        if ecart_pct > 5:
            tooltip_text += "<br><br><span style='color:orange;'>⚠️ Incohérence calorique détectée</span>"

        alim_label.setToolTip(tooltip_text)

        # Ajouter le widget conteneur au layout parent
        parent_layout.addWidget(alim_container)

    def update_aliment_weight(self, aliment_id, new_quantity):
        """Met à jour le poids d'un aliment dans le repas"""
        # Mettre à jour la base de données
        self.db_manager.modifier_quantite_aliment_repas(
            self.repas_data["id"], aliment_id, new_quantity
        )

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

    def modifier_multiplicateur(self):
        """Ouvre une boîte de dialogue pour modifier le multiplicateur du repas"""
        # Récupérer les infos actuelles
        repas_multi_info = self.db_manager.get_repas_multiplicateur(
            self.repas_data["id"]
        )
        multiplicateur_actuel = repas_multi_info.get("multiplicateur", 1)
        ignore_actuel = repas_multi_info.get("ignore_course", False)

        dialog = QDialog(self)
        dialog.setWindowTitle("Paramètres pour la liste de courses")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        # Titre explicatif
        titre = QLabel("<b>Comment traiter ce repas dans la liste de courses ?</b>")
        layout.addWidget(titre)

        # Options
        group = QButtonGroup(dialog)

        # Option 1: Quantité normale
        option_normale = QRadioButton("Quantité normale (×1)")
        option_normale.setChecked(not ignore_actuel and multiplicateur_actuel == 1)
        group.addButton(option_normale)
        layout.addWidget(option_normale)

        # Option 2: Multiplier les quantités
        option_multi_container = QHBoxLayout()
        option_multi = QRadioButton("Multiplier les quantités par:")
        option_multi.setChecked(not ignore_actuel and multiplicateur_actuel > 1)
        group.addButton(option_multi)
        option_multi_container.addWidget(option_multi)

        self.multi_spin.setProperty("class", "spin-box-vertical")
        self.multi_spin.setMinimum(2)
        self.multi_spin.setMaximum(10)
        self.multi_spin.setValue(max(2, multiplicateur_actuel))
        option_multi_container.addWidget(self.multi_spin)
        option_multi_container.addWidget(self.multi_spin)

        layout.addLayout(option_multi_container)

        # Option 3: Déjà préparé
        option_ignore = QRadioButton("Ce repas est déjà préparé (ne pas l'inclure)")
        option_ignore.setChecked(ignore_actuel)
        group.addButton(option_ignore)
        layout.addWidget(option_ignore)

        # Boutons standard
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        # Exécuter la boîte de dialogue
        if dialog.exec():
            # Récupérer les valeurs
            if option_normale.isChecked():
                multiplicateur = 1
                ignore_course = False
            elif option_multi.isChecked():
                multiplicateur = self.multi_spin.value()
                ignore_course = False
            else:  # option_ignore
                multiplicateur = 1
                ignore_course = True

            # Sauvegarder les modifications
            self.db_manager.set_repas_multiplicateur(
                self.repas_data["id"],
                multiplicateur=multiplicateur,
                ignore_course=ignore_course,
            )

            # Mettre à jour l'apparence du bouton
            if ignore_course:
                self.btn_multi.setText("Préparé")
                self.btn_multi.setStyleSheet("background-color: #4CAF50; color: white;")
                self.btn_multi.setToolTip(
                    "Déjà préparé - n'apparaît pas dans la liste de courses"
                )
            else:
                self.btn_multi.setText(f"× {multiplicateur}")
                if multiplicateur > 1:
                    self.btn_multi.setStyleSheet(
                        "background-color: #2196F3; color: white;"
                    )
                    self.btn_multi.setToolTip(
                        f"Quantités multipliées par {multiplicateur} dans la liste de courses"
                    )
                else:
                    self.btn_multi.setStyleSheet("")
                    self.btn_multi.setToolTip(
                        "Cliquez pour modifier la quantité dans la liste de courses"
                    )

            # Notifier que les repas ont été modifiés
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

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

            # Ajouter directement tous les aliments sans zone de défilement
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
        # Calculer les calories à partir des macros
        calories_calcules = (
            self.repas_data["total_proteines"] * 4
            + self.repas_data["total_glucides"] * 4
            + self.repas_data["total_lipides"] * 9
        )

        # Calculer l'écart en pourcentage
        calories_affiches = self.repas_data["total_calories"]
        if calories_calcules > 0:
            ecart_pct = (
                abs(calories_affiches - calories_calcules) / calories_calcules * 100
            )
        else:
            ecart_pct = 0

        # Nettoyer le layout d'en-tête et recréer les éléments
        # Trouver le layout des calories dans le layout principal
        header_layout = None
        for i in range(self.repas_layout.count()):
            item = self.repas_layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                header_layout = item
                break

        if header_layout:
            # Trouver le layout calories + alerte
            calories_alert_layout = None
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if isinstance(item, QHBoxLayout) and item.count() > 0:
                    # Vérifier si le premier widget est un QLabel avec la classe "calories-label"
                    widget = item.itemAt(0).widget()
                    if (
                        isinstance(widget, QLabel)
                        and widget.property("class") == "calories-label"
                    ):
                        calories_alert_layout = item
                        break

            if calories_alert_layout:
                # Mettre à jour le texte des calories
                calories_label = calories_alert_layout.itemAt(0).widget()
                calories_label.setText(f"{self.repas_data['total_calories']:.0f} kcal")

                # Supprimer l'ancien indicateur d'alerte s'il existe
                if calories_alert_layout.count() > 1:
                    item = calories_alert_layout.itemAt(1)
                    if item.widget():
                        item.widget().deleteLater()
                        calories_alert_layout.removeItem(item)

                # Ajouter un nouvel indicateur d'alerte si nécessaire
                if ecart_pct > 5:
                    alert_icon = QLabel("⚠️")
                    alert_icon.setProperty("warning-icon", True)

                    # Créer un tooltip détaillé
                    diff = calories_affiches - calories_calcules
                    signe = "+" if diff > 0 else ""
                    tooltip = (
                        f"<b>Attention</b>: Incohérence calorique détectée<br>"
                        f"Calories affichées: <b>{calories_affiches:.0f} kcal</b><br>"
                        f"Calories des macros: <b>{calories_calcules:.0f} kcal</b><br>"
                        f"Différence: <b>{signe}{diff:.0f} kcal</b> ({ecart_pct:.1f}%)<br><br>"
                        f"Cela peut indiquer une erreur dans les valeurs nutritionnelles des aliments."
                    )
                    alert_icon.setToolTip(tooltip)
                    calories_alert_layout.addWidget(alert_icon)

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

    def enterEvent(self, event):  # pylint: disable=invalid-name
        """Se déclenche quand la souris entre dans le widget"""
        # Changer le curseur en main ouverte pour indiquer qu'on peut faire un drag
        self.setCursor(Qt.OpenHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):  # pylint: disable=invalid-name
        """Se déclenche quand la souris quitte le widget"""
        # Restaurer le curseur par défaut
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """Capture la position de départ pour potentiellement démarrer un drag"""
        if event.button() == Qt.LeftButton:
            # Enregistrer la position de départ pour la comparer plus tard
            self.drag_start_position = event.pos()
            self.is_dragging = False
            self.setCursor(Qt.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """Démarre le drag seulement si la souris a suffisamment bougé"""
        if not event.buttons() & Qt.LeftButton:
            return

        if self.drag_start_position is None or self.is_dragging:
            return

        distance = (event.pos() - self.drag_start_position).manhattanLength()

        if distance < self.drag_threshold:
            return

        # Créer des copies locales des données importantes pour éviter les références
        # qui pourraient être invalidées plus tard
        local_repas_id = self.repas_data["id"]
        local_jour = self.jour

        self.is_dragging = True
        drag = QDrag(self)
        mime_data = QMimeData()

        # Données essentielles pour le drop: ID du repas et jour d'origine
        data = QByteArray(f"{local_repas_id}|{local_jour}".encode())
        mime_data.setData("application/x-repas", data)
        drag.setMimeData(mime_data)

        # Capturer l'image du widget (légèrement plus petite pour l'effet visuel)
        pixmap = self.grab()

        # Créer une version semi-transparente de l'image
        transparent_pixmap = QPixmap(pixmap.size())
        transparent_pixmap.fill(Qt.transparent)

        painter = QPainter(transparent_pixmap)
        painter.setOpacity(0.7)  # Un peu moins transparent (70% opaque)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        # Utiliser l'image semi-transparente pour le drag
        drag.setPixmap(transparent_pixmap)

        # Point d'ancrage légèrement décalé vers le haut pour une meilleure visibilité
        drag.setHotSpot(QPoint(event.pos().x(), 5))

        self.setCursor(Qt.ClosedHandCursor)

        # Garder une référence à tous les objets pendant l'exécution
        self._drag_object = drag
        self._mime_data = mime_data
        self._pixmap = transparent_pixmap

        # Exécuter le drag et nettoyer ensuite
        try:
            drag.exec(Qt.MoveAction)
        finally:
            self.is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
            # Supprimer les références pour libérer la mémoire
            del self._drag_object
            del self._mime_data
            del self._pixmap

    def mouseReleaseEvent(self, event):  # pylint: disable=invalid-name
        """Réinitialise les variables de suivi du drag"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
            self.is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
            QApplication.restoreOverrideCursor()

        super().mouseReleaseEvent(event)

    def correct_aliment_nutritional_values(self, aliment):
        """Ouvre un dialogue pour corriger les valeurs nutritionnelles d'un aliment"""
        # Vérifier que l'aliment existe
        if not aliment or "id" not in aliment:
            print("Erreur: Aliment incorrect ou invalide")
            return

        try:
            # Mémoriser explicitement l'état d'expansion avant tout
            was_expanded = self.is_expanded
            print(f"État d'expansion avant correction: {was_expanded}")  # Pour debug

            # Récupérer les données complètes de l'aliment depuis la base de données
            aliment_complet = self.db_manager.get_aliment(aliment["id"])

            # Ouvrir le dialogue de correction
            dialog = CorrectionNutritionDialog(self, aliment_complet, self.db_manager)

            if dialog.exec():
                # Récupérer les valeurs mises à jour
                updated_values = dialog.get_updated_values()

                # Mettre à jour l'aliment dans la base de données
                aliment_updated = {
                    "id": aliment["id"],
                    "nom": aliment_complet["nom"],
                    "marque": aliment_complet["marque"],
                    "magasin": aliment_complet["magasin"],
                    "categorie": aliment_complet["categorie"],
                    "calories": updated_values["calories"],
                    "proteines": updated_values["proteines"],
                    "glucides": updated_values["glucides"],
                    "lipides": updated_values["lipides"],
                    "fibres": aliment_complet["fibres"],
                    "prix_kg": aliment_complet["prix_kg"],
                }

                self.db_manager.modifier_aliment(aliment["id"], aliment_updated)

                # Émettre un signal pour informer que l'aliment a été modifié
                EVENT_BUS.aliments_modifies.emit()

                # Recharger les données du repas
                repas_updated = self.db_manager.get_repas(self.repas_data["id"])
                if repas_updated:
                    # Mettre à jour les données (sans changer l'état d'expansion)
                    self.repas_data = repas_updated

                    # Reconstruire l'interface
                    self.clear_and_rebuild_details()
                    self.update_summaries()

                    # Forcer explicitement l'état d'expansion précédent
                    if was_expanded:
                        # Ne pas modifier self.is_expanded ici - le faire après avoir rendu visible
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
                        # Mettre à jour l'état d'expansion après avoir modifié l'interface
                        self.is_expanded = True
                    else:
                        # Si ce n'était pas expanded, assurez-vous que c'est bien fermé
                        self.details_widget.setVisible(False)
                        self.expand_btn.setStyleSheet("")
                        self.is_expanded = False

                    print(
                        f"État d'expansion après correction: {self.is_expanded}"
                    )  # Pour debug

                    # Mettre à jour les totaux du jour parent
                    self.notify_parent_day_widget()

        except (
            KeyError,
            ValueError,
            AttributeError,
        ) as e:  # Replace with specific exceptions
            print(f"Erreur lors de la correction des valeurs nutritionnelles: {e}")
            traceback.print_exc()  # Affiche la stack trace complète
