from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QApplication,
    QMessageBox,
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPoint, QThread, QPropertyAnimation, QEasingCurve

from src.utils import EVENT_BUS
from src.utils.planning_worker import PlanningOperationWorker
from src.ui.dialogs.repas_dialog import RepasDialog
from src.ui.widgets.repas_widget import RepasWidget
from src.ui.widgets.totaux_macros_widget import TotauxMacrosWidget


class JourWidget(QWidget):
    """Widget représentant un jour de la semaine"""

    THRESHOLD_OVER = 1.1  # Plus de 110%
    THRESHOLD_GOOD_UPPER = 1.1  # Limite supérieure pour "bon"
    THRESHOLD_GOOD_LOWER = 0.9  # Limite inférieure pour "bon"
    THRESHOLD_LOW = 0.5  # Seuil pour "bas"

    def __init__(self, db_manager, jour, repas_list, objectifs_utilisateur, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.jour = jour
        self.repas_list = repas_list
        self.objectifs_utilisateur = objectifs_utilisateur
        self.semaine_id = semaine_id

        # Initialisation d'attributs pour éviter les avertissements W0201
        self.thread = None
        self.worker = None
        self.loading_overlay = None
        self.loading_label = None
        self.animation = None
        self.drop_index = -1

        # Initialisation des attributs UI qui seront définis dans setup_ui
        self.layout = None
        self.titre_jour = None
        self.totaux_widget = None
        self.macros_container = None
        self.separator = None
        self.toggle_macros_btn = None
        self.cal_badge = None
        self.prot_badge = None
        self.gluc_badge = None
        self.lip_badge = None
        self.scroll_area = None
        self.repas_container = None
        self.repas_layout = None
        self.repas_widgets = []

        # Configuration pour le drag & drop
        self.setAcceptDrops(True)

        # Configuration de l'UI
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur du widget jour"""
        # Configuration du layout principal
        self._setup_main_layout()

        # Configuration du header (titre et bouton d'ajout)
        self._setup_header()

        # Configuration des totaux et des badges de macros
        self._setup_macros_display()

        # Configuration de la zone de repas
        self._setup_meals_area()

    def _setup_main_layout(self):
        """Configure le layout principal du widget"""
        self.setMaximumWidth(350)
        self.setMinimumWidth(275)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)

    def _setup_header(self):
        """Configure l'en-tête du jour avec le titre et le bouton d'ajout"""
        jour_header = QHBoxLayout()
        self.titre_jour = QLabel(f"<h2>{self.jour}</h2>")
        jour_header.addWidget(self.titre_jour)

        # Bouton pour ajouter un repas à ce jour
        btn_add_day = QPushButton("✚ Ajouter un repas")
        btn_add_day.setObjectName("addMealButton")
        btn_add_day.setToolTip(f"Ajouter un repas le {self.jour}")
        btn_add_day.clicked.connect(self.add_meal)
        jour_header.addWidget(btn_add_day)

        self.layout.addLayout(jour_header)

    def _setup_macros_display(self):
        """Configure l'affichage des macros nutritionnelles et des totaux"""
        # Calculer les totaux nutritionnels pour ce jour
        total_cal, total_prot, total_gluc, total_lip, total_cout = (
            self._calculate_totals()
        )

        # Créer un conteneur pour les totaux du jour avec un en-tête dépliable
        macros_container = QWidget()
        macros_layout = QVBoxLayout(macros_container)
        macros_layout.setContentsMargins(0, 5, 0, 0)
        macros_layout.setSpacing(2)

        # En-tête des macros avec résumé compact et bouton pour déplier
        header_layout = self._create_macros_header(
            total_cal, total_prot, total_gluc, total_lip
        )
        macros_layout.addLayout(header_layout)

        # Créer le widget des totaux (caché par défaut)
        self.totaux_widget = TotauxMacrosWidget(
            total_cal,
            total_prot,
            total_gluc,
            total_lip,
            total_cout,
            self.objectifs_utilisateur,
            compact=True,
        )
        self.totaux_widget.setVisible(False)  # Caché par défaut
        macros_layout.addWidget(self.totaux_widget)

        # Ajouter le conteneur au layout principal
        self.layout.addWidget(macros_container)

        # Garder une référence pour les mises à jour ultérieures
        self.macros_container = macros_container

        # Séparateur visuel entre les totaux et les repas
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.separator)

    def _create_macros_header(self, total_cal, total_prot, total_gluc, total_lip):
        """Crée l'en-tête des macros avec les badges et le bouton de déplier/replier"""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Calculer les pourcentages pour déterminer les couleurs des badges
        percent_cal = (
            total_cal / self.objectifs_utilisateur["calories"]
            if self.objectifs_utilisateur["calories"] > 0
            else 0
        )
        percent_prot = (
            total_prot / self.objectifs_utilisateur["proteines"]
            if self.objectifs_utilisateur["proteines"] > 0
            else 0
        )
        percent_gluc = (
            total_gluc / self.objectifs_utilisateur["glucides"]
            if self.objectifs_utilisateur["glucides"] > 0
            else 0
        )
        percent_lip = (
            total_lip / self.objectifs_utilisateur["lipides"]
            if self.objectifs_utilisateur["lipides"] > 0
            else 0
        )

        # Widget conteneur pour tous les badges
        badges_container = QWidget()
        badges_layout = QHBoxLayout(badges_container)
        badges_layout.setContentsMargins(0, 0, 0, 0)
        badges_layout.setSpacing(4)

        # Badge des calories
        cal_badge = QLabel(f"{total_cal:.0f} kcal")
        cal_badge.setProperty("class", "macro-badge")
        cal_badge.setProperty("type", "calories")
        cal_badge.setProperty("status", self._get_status_class(percent_cal))
        badges_layout.addWidget(cal_badge)

        # Badge des protéines
        prot_badge = QLabel(f"P: {total_prot:.0f}g")
        prot_badge.setProperty("class", "macro-badge")
        prot_badge.setProperty("type", "proteines")
        prot_badge.setProperty("status", self._get_status_class(percent_prot))
        badges_layout.addWidget(prot_badge)

        # Badge des glucides
        gluc_badge = QLabel(f"G: {total_gluc:.0f}g")
        gluc_badge.setProperty("class", "macro-badge")
        gluc_badge.setProperty("type", "glucides")
        gluc_badge.setProperty("status", self._get_status_class(percent_gluc))
        badges_layout.addWidget(gluc_badge)

        # Badge des lipides
        lip_badge = QLabel(f"L: {total_lip:.0f}g")
        lip_badge.setProperty("class", "macro-badge")
        lip_badge.setProperty("type", "lipides")
        lip_badge.setProperty("status", self._get_status_class(percent_lip))
        badges_layout.addWidget(lip_badge)

        # Ajouter le conteneur de badges au layout principal
        header_layout.addWidget(badges_container, 1)  # 1 = stretch factor

        # Bouton pour déplier/replier (à droite, sans stretch)
        self.toggle_macros_btn = QPushButton("▼")
        self.toggle_macros_btn.setObjectName("toggleMacrosButton")
        self.toggle_macros_btn.setFixedSize(24, 24)
        self.toggle_macros_btn.setToolTip("Afficher/masquer les détails nutritionnels")
        self.toggle_macros_btn.clicked.connect(self.toggle_macros_details)
        header_layout.addWidget(self.toggle_macros_btn, 0)  # 0 = pas de stretch

        # Garder une référence pour les mises à jour ultérieures
        self.cal_badge = cal_badge
        self.prot_badge = prot_badge
        self.gluc_badge = gluc_badge
        self.lip_badge = lip_badge

        return header_layout

    def _calculate_totals(self):
        """Calcule tous les totaux nutritionnels pour ce jour"""
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0
        total_cout = 0

        # Calculer les totaux pour les repas
        for repas in self.repas_list:
            total_cal += repas["total_calories"]
            total_prot += repas["total_proteines"]
            total_gluc += repas["total_glucides"]
            total_lip += repas["total_lipides"]

            for aliment in repas["aliments"]:
                # prix_kg est en € par kg, donc on divise par 1000 pour avoir € par g
                # puis on multiplie par la quantité en grammes
                if aliment.get("prix_kg"):
                    total_cout += (aliment["prix_kg"] / 1000) * aliment["quantite"]

        return total_cal, total_prot, total_gluc, total_lip, total_cout

    def _setup_meals_area(self):
        """Configure la zone d'affichage des repas avec défilement"""
        # Créer un QScrollArea pour contenir uniquement les repas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)  # Pas de bordure
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )  # Désactiver la barre horizontale

        # Container pour les repas avec prise en charge de l'indicateur de drop
        self.repas_container = RepasContainer()
        self.repas_layout = QVBoxLayout(self.repas_container)
        self.repas_layout.setContentsMargins(0, 0, 0, 0)
        self.repas_layout.setSpacing(5)

        # Assurer que le conteneur s'adapte à la largeur disponible
        self.repas_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Ajouter les repas du jour au conteneur défilable
        self._add_meal_widgets()

        # Configurer le scroll area avec le container de repas
        self.scroll_area.setWidget(self.repas_container)

        # Ajouter le scroll area au layout principal
        self.layout.addWidget(
            self.scroll_area, 1
        )  # Le 1 donne un stretch pour que le scroll area prenne l'espace disponible

    def _add_meal_widgets(self):
        """Ajoute les widgets de repas au conteneur"""
        self.repas_widgets = []
        for repas in self.repas_list:
            repas_widget = RepasWidget(
                self.db_manager,
                repas,
                self.semaine_id,
                self.jour,
                compact_mode=True,  # Activez le mode compact par défaut
            )
            repas_widget.setObjectName(f"repas_{repas['id']}")
            self.repas_layout.addWidget(repas_widget)
            self.repas_widgets.append(repas_widget)

        # Ajouter un espacement extensible en bas
        self.repas_layout.addStretch()

    def _get_status_class(self, percentage):
        """Détermine la classe CSS à utiliser en fonction du pourcentage de l'objectif atteint"""
        if percentage > self.THRESHOLD_OVER:
            return "over"
        elif self.THRESHOLD_GOOD_LOWER <= percentage <= self.THRESHOLD_GOOD_UPPER:
            return "good"
        elif self.THRESHOLD_LOW <= percentage <= self.THRESHOLD_GOOD_LOWER:
            return "medium"
        elif percentage <= self.THRESHOLD_LOW:
            return "low"

    def toggle_macros_details(self):
        """Affiche ou masque les détails des macros avec une animation"""
        is_visible = self.totaux_widget.isVisible()

        # Créer l'animation pour une transition fluide
        # Vérifier si l'animation existe et est en cours d'exécution
        if (
            self.animation is not None
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        # L'animation doit utiliser maximumHeight pour éviter les problèmes de layout
        self.animation = QPropertyAnimation(self.totaux_widget, b"maximumHeight")
        self.animation.setDuration(150)  # 150ms - rapide mais visible
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # Obtenir la hauteur cible avant de commencer l'animation
        target_height = self.totaux_widget.sizeHint().height()

        if is_visible:
            # Animation de fermeture - IMPORTANT: maintenir la visibilité pendant l'animation
            self.animation.setStartValue(self.totaux_widget.height())
            self.animation.setEndValue(0)

            # Uniquement masquer après la fin de l'animation
            self.animation.finished.connect(
                lambda: self.totaux_widget.setVisible(False)
            )
            self.toggle_macros_btn.setText("▼")
        else:
            # Animation d'ouverture - définir la hauteur maximale à 0 avant de rendre visible
            self.totaux_widget.setMaximumHeight(0)
            self.totaux_widget.setVisible(True)

            # S'assurer que le widget a une hauteur préférée correcte
            self.totaux_widget.adjustSize()

            # Commencer l'animation
            self.animation.setStartValue(0)
            self.animation.setEndValue(target_height)
            self.toggle_macros_btn.setText("▲")

        # Connecter une fonction pour ajuster le layout pendant l'animation
        self.animation.valueChanged.connect(self._on_animation_update)
        self.animation.start()

    def _on_animation_update(self, _):
        """Appelé pendant l'animation pour s'assurer que le layout reste stable"""
        # Forcer la mise à jour du layout pour éviter les sauts
        self.macros_container.layout().activate()
        self.layout.activate()

        # Mettre à jour le conteneur parent
        if self.parent():
            self.parent().update()

    def add_meal(self):
        """Ajoute un repas pour ce jour"""
        # Déterminer le prochain ordre disponible
        max_ordre = 0
        for repas in self.repas_list:
            if repas["ordre"] > max_ordre:
                max_ordre = repas["ordre"]

        # Le nouvel ordre sera le maximum actuel + 1
        next_ordre = max_ordre + 1

        dialog = RepasDialog(
            self,
            self.db_manager,
            self.semaine_id,
            jour_predefini=self.jour,
            ordre_predefini=next_ordre,
        )

        if dialog.exec():
            nom, jour, ordre, repas_type_id = dialog.get_data()

            # Si l'utilisateur a choisi un ordre différent de celui suggéré,
            # décaler les repas existants pour faire de la place
            if ordre != next_ordre:
                # Vérifier si l'ordre existe déjà
                existe_deja = False
                for repas in self.repas_list:
                    if repas["ordre"] == ordre:
                        existe_deja = True
                        break

                # Si l'ordre existe déjà, décaler les repas
                if existe_deja:
                    self.db_manager.decaler_ordres(jour, self.semaine_id, ordre)

            if repas_type_id:
                # Utiliser une recette existante MAIS conserver le nom personnalisé
                self.db_manager.appliquer_repas_type_au_jour(
                    repas_type_id, jour, ordre, self.semaine_id, nom_personnalise=nom
                )
            else:
                # Créer un nouveau repas vide
                self.db_manager.ajouter_repas(nom, jour, ordre, self.semaine_id)

            # Normaliser les ordres après l'ajout pour garantir des ordres consécutifs
            self.db_manager.normaliser_ordres(jour, self.semaine_id)

            # Émettre le signal pour notifier que les repas ont été modifiés
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

            # Notifier le widget parent pour recharger les données
            parent = self.parent()
            if parent and hasattr(parent, "load_data"):
                parent.load_data()

    def update_objectifs(self, objectifs):
        """Met à jour les objectifs nutritionnels"""
        self.objectifs_utilisateur = objectifs

        # Calculer les totaux
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0
        total_cout = 0

        for repas in self.repas_list:
            total_cal += repas["total_calories"]
            total_prot += repas["total_proteines"]
            total_gluc += repas["total_glucides"]
            total_lip += repas["total_lipides"]

            # Calculer le coût total
            for aliment in repas["aliments"]:
                if aliment.get("prix_kg"):
                    total_cout += (aliment["prix_kg"] / 1000) * aliment["quantite"]

        # Calculer les pourcentages
        percent_cal = (
            total_cal / self.objectifs_utilisateur["calories"]
            if self.objectifs_utilisateur["calories"] > 0
            else 0
        )
        percent_prot = (
            total_prot / self.objectifs_utilisateur["proteines"]
            if self.objectifs_utilisateur["proteines"] > 0
            else 0
        )
        percent_gluc = (
            total_gluc / self.objectifs_utilisateur["glucides"]
            if self.objectifs_utilisateur["glucides"] > 0
            else 0
        )
        percent_lip = (
            total_lip / self.objectifs_utilisateur["lipides"]
            if self.objectifs_utilisateur["lipides"] > 0
            else 0
        )

        # Mettre à jour les badges
        self.cal_badge.setText(f"{total_cal:.0f} kcal")
        self.cal_badge.setProperty("status", self._get_status_class(percent_cal))

        self.prot_badge.setText(f"P: {total_prot:.0f}g")
        self.prot_badge.setProperty("status", self._get_status_class(percent_prot))

        self.gluc_badge.setText(f"G: {total_gluc:.0f}g")
        self.gluc_badge.setProperty("status", self._get_status_class(percent_gluc))

        self.lip_badge.setText(f"L: {total_lip:.0f}g")
        self.lip_badge.setProperty("status", self._get_status_class(percent_lip))

        # Forcer la mise à jour du style
        self.cal_badge.style().polish(self.cal_badge)
        self.prot_badge.style().polish(self.prot_badge)
        self.gluc_badge.style().polish(self.gluc_badge)
        self.lip_badge.style().polish(self.lip_badge)

        # Mettre à jour le widget des totaux
        self.totaux_widget.update_values(
            total_cal,
            total_prot,
            total_gluc,
            total_lip,
            total_cout,
            self.objectifs_utilisateur,
        )

    def get_expanded_repas_ids(self):
        """Récupère la liste des IDs des repas qui sont actuellement ouverts"""
        expanded_ids = set()

        # Parcourir tous les widgets de repas dans le layout
        for i in range(self.repas_layout.count()):
            item = self.repas_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, RepasWidget) and widget.is_expanded:
                    expanded_ids.add(widget.repas_data["id"])

        return expanded_ids

    def update_day_totals(self):
        """Met à jour uniquement les totaux du jour sans recharger les repas"""
        # Calculer les nouveaux totaux
        total_calories = 0
        total_proteines = 0
        total_glucides = 0
        total_lipides = 0
        total_cout = 0

        # Parcourir tous les widgets de repas
        for i in range(self.repas_layout.count()):
            item = self.repas_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, RepasWidget):
                    # Ajouter les valeurs nutritionnelles
                    total_calories += widget.repas_data["total_calories"]
                    total_proteines += widget.repas_data["total_proteines"]
                    total_glucides += widget.repas_data["total_glucides"]
                    total_lipides += widget.repas_data["total_lipides"]

                    # Calculer le coût
                    for aliment in widget.repas_data["aliments"]:
                        if aliment.get("prix_kg"):
                            total_cout += (aliment["prix_kg"] / 1000) * aliment[
                                "quantite"
                            ]

        # Calculer les pourcentages pour déterminer les couleurs
        percent_cal = (
            total_calories / self.objectifs_utilisateur["calories"]
            if self.objectifs_utilisateur["calories"] > 0
            else 0
        )
        percent_prot = (
            total_proteines / self.objectifs_utilisateur["proteines"]
            if self.objectifs_utilisateur["proteines"] > 0
            else 0
        )
        percent_gluc = (
            total_glucides / self.objectifs_utilisateur["glucides"]
            if self.objectifs_utilisateur["glucides"] > 0
            else 0
        )
        percent_lip = (
            total_lipides / self.objectifs_utilisateur["lipides"]
            if self.objectifs_utilisateur["lipides"] > 0
            else 0
        )

        # Mettre à jour les badges
        self.cal_badge.setText(f"{total_calories:.0f} kcal")
        self.cal_badge.setProperty("status", self._get_status_class(percent_cal))

        self.prot_badge.setText(f"P: {total_proteines:.0f}g")
        self.prot_badge.setProperty("status", self._get_status_class(percent_prot))

        self.gluc_badge.setText(f"G: {total_glucides:.0f}g")
        self.gluc_badge.setProperty("status", self._get_status_class(percent_gluc))

        self.lip_badge.setText(f"L: {total_lipides:.0f}g")
        self.lip_badge.setProperty("status", self._get_status_class(percent_lip))

        # Forcer la mise à jour du style
        self.cal_badge.style().polish(self.cal_badge)
        self.prot_badge.style().polish(self.prot_badge)
        self.gluc_badge.style().polish(self.gluc_badge)
        self.lip_badge.style().polish(self.lip_badge)

        # Mettre à jour le widget des totaux détaillés
        self.totaux_widget.update_values(
            total_calories,
            total_proteines,
            total_glucides,
            total_lipides,
            total_cout,
            self.objectifs_utilisateur,
        )

    def dragEnterEvent(self, event):  # pylint: disable=invalid-name
        """Gère l'entrée d'un drag dans la zone du jour"""
        if event.mimeData().hasFormat("application/x-repas"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):  # pylint: disable=invalid-name
        """Gère le déplacement d'un drag sur la zone du jour"""
        if event.mimeData().hasFormat("application/x-repas"):
            # Déterminer l'emplacement où le repas sera déposé
            pos = event.position()

            # Ignorer le drag si c'est au-dessus du header ou des totaux
            header_height = (
                self.titre_jour.height()
                + self.macros_container.height()
                + self.separator.height()
            )
            if pos.y() < header_height:
                self.drop_index = -1
                self.repas_container.set_drop_indicator(None)
                event.ignore()
                return

            # Ajuster la position pour le conteneur de repas
            container_pos = self.scroll_area.mapFrom(
                self, QPoint(int(pos.x()), int(pos.y()))
            )
            scroll_pos = self.repas_container.mapFrom(self.scroll_area, container_pos)

            # Déterminer l'index où insérer le repas
            index = -1
            drop_position = None

            # Si la liste des repas est vide, placer l'indicateur en haut du conteneur
            if not self.repas_widgets:
                index = 0
                drop_position = QPoint(0, 10)  # Plus visible en haut du conteneur vide
            else:
                # Traitement spécial pour la position au-dessus du premier repas
                first_widget = self.repas_widgets[0]
                if scroll_pos.y() < first_widget.y() + 15:  # Zone de tolérance en haut
                    index = 0
                    drop_position = QPoint(0, max(5, first_widget.y() - 5))
                    self.drop_index = index
                    self.repas_container.set_drop_indicator(drop_position)
                    self.repas_container.update()
                    event.acceptProposedAction()
                    return

                # Parcourir les widgets de repas pour trouver l'emplacement
                for i, repas_widget in enumerate(self.repas_widgets):
                    widget_top = repas_widget.y()
                    widget_height = repas_widget.height()
                    widget_bottom = widget_top + widget_height

                    # Position relative dans le widget (0 = haut, 1 = bas)
                    relative_pos = (scroll_pos.y() - widget_top) / widget_height

                    # Si on est dans la zone supérieure (30% du haut)
                    if 0 <= relative_pos < 0.3:
                        index = i
                        drop_position = QPoint(0, widget_top - 3)
                        break
                    # Si on est dans la zone inférieure (30% du bas)
                    elif 0.7 < relative_pos <= 1:
                        index = i + 1
                        drop_position = QPoint(0, widget_bottom + 3)
                        break

                # Si aucune position n'est trouvée (dans la zone centrale d'un repas)
                # on ne montre pas d'indicateur de drop
                if index == -1:
                    self.drop_index = -1
                    self.repas_container.set_drop_indicator(None)
                    event.acceptProposedAction()  # On accepte quand même l'action pour ne pas perturber le drag
                    return

            # Mettre à jour l'indicateur de drop et l'index
            self.drop_index = index
            self.repas_container.set_drop_indicator(drop_position)
            self.repas_container.update()

            event.acceptProposedAction()
        else:
            self.drop_index = -1
            self.repas_container.set_drop_indicator(None)
            event.ignore()

    def dragLeaveEvent(self, event):  # pylint: disable=invalid-name
        """Gère la sortie d'un drag de la zone du jour"""
        self._cleanup_after_drag()
        super().dragLeaveEvent(event)

    def _cleanup_after_drag(self):
        """Nettoie l'interface après une opération de drag & drop"""
        self.drop_index = -1
        self.repas_container.set_drop_indicator(None)
        self.repas_container.update()
        return True

    def dropEvent(self, event):  # pylint: disable=invalid-name
        """Gère le drop d'un repas dans le jour avec détection d'annulation"""
        if event.mimeData().hasFormat("application/x-repas"):
            try:
                data = event.mimeData().data("application/x-repas").data().decode()
                parts = data.split("|")
                if len(parts) != 2:
                    raise ValueError("Format de données invalide")
                repas_id, jour_origine = parts
                repas_id = int(repas_id)
            except (ValueError, IndexError) as e:
                print(f"Erreur lors du parsing des données de drag & drop: {e}")
                event.ignore()
                return

            # Vérifier si on déplace le repas au même jour
            meme_jour = jour_origine == self.jour

            # Trouver le repas qui est déplacé
            repas_deplace = None
            repas_index = -1

            for i, repas in enumerate(self.repas_list):
                if repas["id"] == repas_id:
                    repas_deplace = repas
                    repas_index = i
                    break

            # Vérifier si on essaie de déplacer à la même position
            meme_position = False

            if meme_jour and repas_deplace is not None and repas_index != -1:
                if self.drop_index == repas_index or self.drop_index == repas_index + 1:
                    meme_position = True

            # Si c'est la même position, ne rien faire
            if meme_position:
                self._cleanup_after_drag()
                event.acceptProposedAction()
                return

            # Trier les repas existants par ordre
            sorted_repas = sorted(self.repas_list, key=lambda r: r.get("ordre", 1))

            # Déterminer le nouvel ordre du repas en fonction de l'indice de drop
            if self.drop_index >= 0:
                if len(sorted_repas) == 0:
                    # Si aucun repas, mettre ordre 1
                    nouvel_ordre = 1
                elif self.drop_index == 0:
                    # Au début, utiliser l'ordre du premier repas - 0.5
                    # ou 1 si c'est le seul repas
                    if sorted_repas[0].get("ordre", 1) > 1:
                        nouvel_ordre = int(sorted_repas[0].get("ordre", 1) - 0.5)
                    else:
                        # Si le premier repas a déjà l'ordre 1, décaler tout
                        nouvel_ordre = 1
                        # Faire de la place
                        self.db_manager.decaler_ordres(self.jour, self.semaine_id, 1)
                elif self.drop_index >= len(sorted_repas):
                    # À la fin, mettre ordre = dernier + 1
                    nouvel_ordre = sorted_repas[-1].get("ordre", 1) + 1
                else:
                    # Au milieu, vérifier si les ordres sont consécutifs
                    ordre_prev = sorted_repas[self.drop_index - 1].get("ordre", 1)
                    ordre_next = sorted_repas[self.drop_index].get("ordre", 1)

                    if ordre_next == ordre_prev + 1:
                        # Si les ordres sont consécutifs, décaler pour faire de la place
                        nouvel_ordre = ordre_next
                        self.db_manager.decaler_ordres(
                            self.jour, self.semaine_id, nouvel_ordre
                        )
                    else:
                        # S'il y a de l'espace entre les ordres, prendre la moyenne
                        nouvel_ordre = int((ordre_prev + ordre_next) / 2)
                        if nouvel_ordre == ordre_prev:  # Si arrondi à ordre_prev
                            nouvel_ordre = ordre_prev + 1
                            if nouvel_ordre == ordre_next:  # Si pas d'espace
                                self.db_manager.decaler_ordres(
                                    self.jour, self.semaine_id, nouvel_ordre
                                )
            else:
                # Fallback: mettre à la fin
                nouvel_ordre = len(sorted_repas) + 1

            # Ajoutez un raffraîchissement explicite après le calcul du nouvel ordre
            self.repas_container.update()

            # Afficher un overlay de chargement et continuer avec le processus existant
            self.show_loading_overlay("Déplacement du repas en cours...")

            # Réinitialiser l'indicateur de drop immédiatement
            self._cleanup_after_drag()

            # Créer et configurer le thread et le worker
            self.thread = QThread()
            self.worker = PlanningOperationWorker(
                self.db_manager,
                "move_repas",
                repas_id=repas_id,
                jour_dest=self.jour,
                ordre_dest=nouvel_ordre,
                semaine_id=self.semaine_id,
            )

            # Configurer les connexions
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.operation_completed.connect(self.on_operation_completed)
            self.worker.operation_completed.connect(self.thread.quit)
            self.worker.operation_completed.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            # Démarrer le thread
            self.thread.start()

            event.acceptProposedAction()
        else:
            event.ignore()

    def show_loading_overlay(self, message="Opération en cours..."):
        """Affiche un overlay de chargement sur le widget"""
        if hasattr(self, "loading_overlay") and self.loading_overlay:
            self.loading_overlay.deleteLater()

        self.loading_overlay = QWidget(self)
        self.loading_overlay.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 50%);
            border-radius: 5px;
        """
        )

        overlay_layout = QVBoxLayout(self.loading_overlay)
        self.loading_label = QLabel(message)
        self.loading_label.setStyleSheet(
            """
            color: white;
            font-weight: bold;
            background-color: rgba(40, 40, 40, 80%);
            border-radius: 5px;
            padding: 10px;
        """
        )
        self.loading_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.loading_label, 0, Qt.AlignCenter)
        overlay_layout.addStretch()
        self.loading_overlay.resize(self.size())
        self.loading_overlay.show()
        self.loading_overlay.raise_()
        QApplication.processEvents()

    def hide_loading_overlay(self):
        """Cache l'overlay de chargement"""
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.hide()

    def on_operation_completed(self, success, message, data):
        """Callback appelé lorsque l'opération est terminée"""
        self.hide_loading_overlay()

        if success:
            # Notifier que les repas ont été modifiés
            semaine_id = data.get("semaine_id") if data else self.semaine_id
            EVENT_BUS.repas_modifies.emit(semaine_id)
            EVENT_BUS.planning_modifie.emit()

            # Recharger les données
            parent = self.parent()
            if parent and hasattr(parent, "load_data"):
                parent.load_data()
        else:
            QMessageBox.warning(self, "Erreur", message)


class RepasContainer(QWidget):
    """Widget conteneur pour les repas avec capacité à dessiner un indicateur de drop"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drop_indicator_position = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_drop_indicator(self, position):
        """Définit la position de l'indicateur de drop"""
        self.drop_indicator_position = position

        if position:
            self.ensureDropIndicatorVisible()

        self.update()

    def paintEvent(self, event):  # pylint: disable=invalid-name
        """Dessine l'indicateur de drop si nécessaire"""
        super().paintEvent(event)

        # Dessiner l'indicateur de drop si nécessaire
        if self.drop_indicator_position:
            painter = QPainter(self)

            # Utiliser l'antialiasing pour des lignes plus nettes
            painter.setRenderHint(QPainter.Antialiasing)

            # Définir le style de la ligne
            pen = QPen(QColor("#2196F3"))  # Bleu plus visible
            pen.setWidth(3)
            pen.setStyle(Qt.SolidLine)  # Ligne pleine au lieu de pointillé
            pen.setCapStyle(Qt.RoundCap)  # Extrémités arrondies
            painter.setPen(pen)

            # Dessiner une ligne horizontale à la position de l'indicateur
            x1 = 10  # Marge gauche
            x2 = self.width() - 20  # Marge droite
            y = self.drop_indicator_position.y()

            # S'assurer que la ligne est visible même si y est très petit (en haut)
            y = max(5, y)

            # Dessiner la ligne principale
            painter.drawLine(x1, y, x2, y)

            # Dessiner des triangles aux extrémités pour indiquer l'insertion
            triangle_size = 5

            # Triangle gauche
            points_left = [
                QPoint(x1, y),
                QPoint(x1 - triangle_size, y - triangle_size),
                QPoint(x1 - triangle_size, y + triangle_size),
            ]
            painter.setBrush(QColor("#2196F3"))
            painter.drawPolygon(points_left)

            # Triangle droit
            points_right = [
                QPoint(x2, y),
                QPoint(x2 + triangle_size, y - triangle_size),
                QPoint(x2 + triangle_size, y + triangle_size),
            ]
            painter.drawPolygon(points_right)

    def resizeEvent(self, event):  # pylint: disable=invalid-name
        """Gère le redimensionnement pour s'assurer que le contenu s'adapte"""
        super().resizeEvent(event)
        self.adjustForScrollBar()

    def showEvent(self, event):  # pylint: disable=invalid-name
        """Gère l'affichage initial du widget"""
        super().showEvent(event)
        self.adjustForScrollBar()

    def adjustForScrollBar(self):  # pylint: disable=invalid-name
        """Ajuste les marges en fonction de la présence de la barre de défilement"""
        if isinstance(self.parent(), QScrollArea):
            # Vérifier si la barre de défilement verticale est visible
            scrollbar_visible = self.parent().verticalScrollBar().isVisible()
            scrollbar_width = (
                self.parent().verticalScrollBar().width() if scrollbar_visible else 0
            )

            # Calculer la marge droite optimale
            right_margin = 3 + scrollbar_width if scrollbar_visible else 3

            # Appliquer les nouvelles marges au layout
            self.layout().setContentsMargins(3, 3, right_margin, 3)

            # Mettre à jour tous les widgets enfants
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, RepasWidget):
                        # Ajuster la largeur maximum
                        widget.setMaximumWidth(
                            self.width() - right_margin - 3
                        )  # -3 pour la marge gauche

    def updateGeometry(self):  # pylint: disable=invalid-name
        """Force la mise à jour de la géométrie et de la taille"""
        super().updateGeometry()

        # Pour les conteneurs avec beaucoup d'éléments, on peut optimiser
        if self.layout().count() > 20:  # Seuil arbitraire
            # Utiliser directement la hauteur du dernier widget visible
            last_visible_widget = None
            last_visible_y = 0

            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item.widget() and item.widget().isVisible():
                    last_visible_widget = item.widget()
                    last_visible_y = (
                        last_visible_widget.y() + last_visible_widget.height()
                    )

            if last_visible_widget:
                self.setMinimumHeight(last_visible_y + 10)  # Ajouter un peu d'espace
        else:
            # Recalculer la taille préférée
            preferred_height = 0
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item.widget() and item.widget().isVisible():
                    preferred_height += (
                        item.widget().sizeHint().height() + self.layout().spacing()
                    )

            # Ajuster la taille du conteneur
            self.setMinimumHeight(preferred_height)

            # Ajuster pour la barre de défilement
            self.adjustForScrollBar()

            # Informer le parent pour ajuster le scroll area
            if self.parent() and isinstance(self.parent(), QScrollArea):
                self.parent().updateGeometry()

    def updateAfterDrag(self):  # pylint: disable=invalid-name
        """Met à jour le widget après un drag pour assurer la cohérence visuelle"""
        # Réinitialiser l'indicateur
        self.set_drop_indicator(None)

        # Recalculer la géométrie
        self.updateGeometry()

        # Forcer une mise à jour visuelle
        self.update()

        # Vérifier l'adaptation à la barre de défilement
        self.adjustForScrollBar()

    def ensureDropIndicatorVisible(self):  # pylint: disable=invalid-name
        """S'assure que l'indicateur de drop est visible"""
        if self.drop_indicator_position:
            # Si l'indicateur est trop haut, l'ajuster légèrement
            if self.drop_indicator_position.y() < 2:
                self.drop_indicator_position = QPoint(
                    self.drop_indicator_position.x(), 2
                )

            # Si le conteneur a un scroll_area parent, s'assurer que la position est visible
            parent = self.parent()
            if isinstance(parent, QScrollArea):
                # Calculer la position de l'indicateur relative au viewport
                viewport_pos = self.mapTo(
                    parent.viewport(), self.drop_indicator_position
                )

                # Si la position est en dehors du viewport visible, faire défiler
                if (
                    viewport_pos.y() < 0
                    or viewport_pos.y() > parent.viewport().height()
                ):
                    parent.ensureVisible(
                        self.drop_indicator_position.x(),
                        self.drop_indicator_position.y(),
                        0,
                        20,
                    )
