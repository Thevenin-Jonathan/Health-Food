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
)
from PySide6.QtCore import Qt, QPoint, QThread
from PySide6.QtGui import QPainter, QColor, QPen
from src.ui.widgets.repas_widget import RepasWidget
from src.ui.widgets.totaux_macros_widget import TotauxMacrosWidget
from src.ui.dialogs.repas_dialog import RepasDialog
from src.utils.events import EVENT_BUS
from src.utils.planning_worker import PlanningOperationWorker


class JourWidget(QWidget):
    """Widget représentant un jour de la semaine"""

    def __init__(self, db_manager, jour, repas_list, objectifs_utilisateur, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.jour = jour
        self.repas_list = repas_list
        self.objectifs_utilisateur = objectifs_utilisateur
        self.semaine_id = semaine_id

        # Variables pour le drag & drop
        self.drop_indicator_position = None
        self.drop_index = -1

        # Accepter les drops
        self.setAcceptDrops(True)

        self.setup_ui()

    def setup_ui(self):
        # Configuration du layout
        self.setMaximumWidth(350)
        self.setMinimumWidth(275)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Titre du jour avec bouton d'ajout
        jour_header = QHBoxLayout()
        titre_jour = QLabel(f"<h2>{self.jour}</h2>")
        jour_header.addWidget(titre_jour)

        # Bouton pour ajouter un repas à ce jour
        btn_add_day = QPushButton("✚ Ajouter un repas")
        btn_add_day.setObjectName("addMealButton")
        btn_add_day.setToolTip(f"Ajouter un repas le {self.jour}")
        btn_add_day.clicked.connect(self.add_meal)
        jour_header.addWidget(btn_add_day)

        self.layout.addLayout(jour_header)

        # Initialiser les totaux du jour
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0
        total_cout = 0

        # Calculer les totaux avant d'ajouter les repas
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

        # Ajouter le widget des totaux AU DÉBUT (avant les repas)
        self.totaux_widget = TotauxMacrosWidget(
            total_cal,
            total_prot,
            total_gluc,
            total_lip,
            total_cout,
            self.objectifs_utilisateur,
            compact=True,
        )
        self.layout.addWidget(self.totaux_widget)

        # Séparateur visuel entre les totaux et les repas
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.separator)

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

        # Configurer le scroll area avec le container de repas
        self.scroll_area.setWidget(self.repas_container)

        # Ajouter le scroll area au layout principal
        self.layout.addWidget(
            self.scroll_area, 1
        )  # Le 1 donne un stretch pour que le scroll area prenne l'espace disponible

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

        # Mettre à jour le widget des totaux
        self.totaux_widget.update_values(
            total_calories,
            total_proteines,
            total_glucides,
            total_lipides,
            total_cout,
            self.objectifs_utilisateur,
        )

    def dragEnterEvent(self, event):
        """Gère l'entrée d'un drag dans la zone du jour"""
        if event.mimeData().hasFormat("application/x-repas"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Gère le déplacement d'un drag sur la zone du jour"""
        if event.mimeData().hasFormat("application/x-repas"):
            # Déterminer l'emplacement où le repas sera déposé
            pos = event.position()

            # Ignorer le drag si c'est au-dessus du header ou des totaux
            if pos.y() < self.totaux_widget.height() + self.separator.height():
                self.drop_indicator_position = None
                self.drop_index = -1
                self.repas_container.set_drop_indicator(None)
                event.ignore()
                return

            # Ajuster la position pour le conteneur de repas
            # Convertir les coordonnées globales en coordonnées du conteneur de repas
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
                drop_position = QPoint(0, 5)  # 5 pixels du haut du conteneur
            else:
                # Parcourir les widgets de repas pour trouver l'emplacement
                for i, repas_widget in enumerate(self.repas_widgets):
                    widget_top = repas_widget.y()
                    widget_bottom = widget_top + repas_widget.height()

                    # Si on est entre deux repas
                    if widget_top <= scroll_pos.y() <= widget_bottom:
                        # Si on est dans la moitié supérieure, insérer avant
                        if scroll_pos.y() < (widget_top + widget_bottom) / 2:
                            index = i
                            drop_position = QPoint(0, widget_top - 5)
                            break
                        # Si on est dans la moitié inférieure, insérer après
                        else:
                            index = i + 1
                            drop_position = QPoint(0, widget_bottom + 5)
                            break
                    # Si on est au-dessus du premier repas
                    elif scroll_pos.y() < widget_top and i == 0:
                        index = 0
                        drop_position = QPoint(0, widget_top - 5)
                        break

                # Si on n'a pas trouvé d'emplacement, c'est qu'on est après le dernier repas
                if index == -1:
                    index = len(self.repas_widgets)
                    if self.repas_widgets:  # Vérifier si la liste n'est pas vide
                        last_widget = self.repas_widgets[-1]
                        drop_position = QPoint(
                            0, last_widget.y() + last_widget.height() + 5
                        )
                    else:
                        drop_position = QPoint(0, 5)

            # Mettre à jour l'indicateur de drop
            self.drop_index = index
            # Mettre à jour directement l'indicateur dans le conteneur
            self.repas_container.set_drop_indicator(drop_position)

            event.acceptProposedAction()
        else:
            self.drop_index = -1
            self.repas_container.set_drop_indicator(None)
            event.ignore()

    def dragLeaveEvent(self, event):
        """Gère la sortie d'un drag de la zone du jour"""
        self.drop_indicator_position = None
        self.drop_index = -1
        if hasattr(self.repas_container, "set_drop_indicator"):
            self.repas_container.set_drop_indicator(None)
        self.update()
        super().dragLeaveEvent(event)

    def dragEndEvent(self, event):
        """Gère la fin d'une opération de drag (qu'elle réussisse ou non)"""
        # Réinitialiser l'indicateur de drop
        self.drop_indicator_position = None
        self.drop_index = -1
        if hasattr(self.repas_container, "set_drop_indicator"):
            self.repas_container.set_drop_indicator(None)
        self.update()

        super().dragEndEvent(event)

    def dropEvent(self, event):
        """Gère le drop d'un repas dans le jour avec détection d'annulation"""
        if event.mimeData().hasFormat("application/x-repas"):
            # Récupérer les données du repas
            data = event.mimeData().data("application/x-repas").data().decode()
            repas_id, jour_origine = data.split("|")
            repas_id = int(repas_id)

            # Vérifier si on déplace le repas au même jour
            meme_jour = jour_origine == self.jour

            # Si nous sommes dans le même jour, vérifier si le repas est déposé au même endroit
            if meme_jour:
                try:
                    # Trouver le repas dans la liste et son ordre actuel
                    repas_actuel = None
                    for repas in self.repas_list:
                        if repas["id"] == repas_id:
                            repas_actuel = repas
                            break

                    if repas_actuel:
                        ordre_actuel = repas_actuel["ordre"]

                        # Déterminer si le repas est déposé à sa position actuelle ou à proximité
                        position_similaire = False

                        # Cas 1: Drop à la même position ou position adjacente
                        if self.drop_index >= 0 and len(self.repas_list) > 0:
                            # Si on dépose à la position actuelle ou juste après
                            if (
                                ordre_actuel == self.drop_index
                                or ordre_actuel == self.drop_index - 1
                            ):
                                position_similaire = True
                            # Si on dépose juste avant
                            elif ordre_actuel == self.drop_index + 1:
                                position_similaire = True

                        # Cas 2: Drop en fin de liste et le repas est déjà le dernier
                        elif self.drop_index == -1 and ordre_actuel == len(
                            self.repas_list
                        ):
                            position_similaire = True

                        if position_similaire:
                            # Réinitialiser l'indicateur de drop sans faire de modifications
                            self.drop_index = -1
                            self.repas_container.set_drop_indicator(None)

                            # Simple rafraîchissement visuel pour réinitialiser l'interface
                            self.update()

                            event.acceptProposedAction()
                            return
                except Exception as e:
                    print(
                        f"Erreur lors de la vérification de la position d'origine: {e}"
                    )
                    # On continue avec le comportement normal en cas d'erreur

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

            # Afficher un overlay de chargement
            self.show_loading_overlay("Déplacement du repas en cours...")

            # Réinitialiser l'indicateur de drop
            self.drop_index = -1
            self.repas_container.set_drop_indicator(None)

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

        if not hasattr(self, "loading_overlay"):
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
        else:
            self.loading_label.setText(message)

        # Redimensionner l'overlay pour couvrir tout le widget
        self.loading_overlay.resize(self.size())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

        # Forcer le rafraîchissement de l'interface
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
            # En cas d'erreur, afficher un message
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Erreur", message)

    def paintEvent(self, event):
        """Surcharge pour dessiner l'indicateur de drop"""
        super().paintEvent(event)

        # Ne rien dessiner si pas en mode drag
        if not self.drop_indicator_position:
            return

        # Note: l'indicateur est maintenant dessiné dans le container de repas


class RepasContainer(QWidget):
    """Widget conteneur pour les repas avec capacité à dessiner un indicateur de drop"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drop_indicator_position = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_drop_indicator(self, position):
        """Définit la position de l'indicateur de drop"""
        self.drop_indicator_position = position
        self.update()

    def paintEvent(self, event):
        """Dessine l'indicateur de drop si nécessaire"""
        super().paintEvent(event)

        # Dessiner l'indicateur de drop si nécessaire
        if self.drop_indicator_position:
            painter = QPainter(self)
            pen = QPen(QColor("#4CAF50"))  # Couleur de l'indicateur
            pen.setWidth(3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)

            # Dessiner une ligne horizontale à la position de l'indicateur
            x1 = 5  # Marge gauche
            x2 = self.width() - 10  # Marge droite
            y = self.drop_indicator_position.y()
            painter.drawLine(x1, y, x2, y)

    def resizeEvent(self, event):
        """Gère le redimensionnement pour s'assurer que le contenu s'adapte"""
        super().resizeEvent(event)
        # S'assurer que les enfants sont bien informés du changement de taille
        for child in self.children():
            if isinstance(child, QWidget):
                child.setMaximumWidth(
                    self.width() - 10
                )  # Marge pour éviter le défilement

    def updateGeometry(self):
        """Force la mise à jour de la géométrie et de la taille"""
        super().updateGeometry()

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

        # Informer le parent pour ajuster le scroll area
        if self.parent() and isinstance(self.parent(), QScrollArea):
            self.parent().updateGeometry()
