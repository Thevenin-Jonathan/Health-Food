from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen
from src.ui.widgets.repas_widget import RepasWidget
from src.ui.widgets.totaux_macros_widget import TotauxMacrosWidget
from src.ui.dialogs.repas_dialog import RepasDialog
from src.utils.events import EVENT_BUS
from src.utils.styles import PRIMARY_COLOR


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
        self.layout = QVBoxLayout(self)

        # Titre du jour avec bouton d'ajout
        jour_header = QHBoxLayout()
        titre_jour = QLabel(f"<h2>{self.jour}</h2>")
        jour_header.addWidget(titre_jour)

        # Bouton pour ajouter un repas à ce jour
        btn_add_day = QPushButton("✚")
        btn_add_day.setObjectName("addButton")
        btn_add_day.setToolTip(f"Ajouter un repas le {self.jour}")
        btn_add_day.clicked.connect(self.add_meal)
        jour_header.addWidget(btn_add_day)

        self.layout.addLayout(jour_header)

        # Initialiser les totaux du jour
        total_cal = 0
        total_prot = 0
        total_gluc = 0
        total_lip = 0

        # Calculer les totaux avant d'ajouter les repas
        for repas in self.repas_list:
            total_cal += repas["total_calories"]
            total_prot += repas["total_proteines"]
            total_gluc += repas["total_glucides"]
            total_lip += repas["total_lipides"]

        # Ajouter le widget des totaux AU DÉBUT (avant les repas)
        self.totaux_widget = TotauxMacrosWidget(
            total_cal,
            total_prot,
            total_gluc,
            total_lip,
            self.objectifs_utilisateur,
            compact=True,
        )
        self.layout.addWidget(self.totaux_widget)

        # Séparateur visuel entre les totaux et les repas
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.separator)

        # Ajouter les repas du jour
        self.repas_widgets = []
        for repas in self.repas_list:
            repas_widget = RepasWidget(
                self.db_manager, repas, self.semaine_id, self.jour
            )
            repas_widget.setObjectName(f"repas_{repas['id']}")
            self.layout.addWidget(repas_widget)
            self.repas_widgets.append(repas_widget)

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
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

            # Notifier le widget parent pour recharger les données
            parent = self.parent()
            if parent and hasattr(parent, "load_data"):
                parent.load_data()

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
            if (
                pos.y()
                < self.totaux_widget.y()
                + self.totaux_widget.height()
                + self.separator.height()
            ):
                self.drop_indicator_position = None
                self.drop_index = -1
                event.ignore()
                return

            # Déterminer l'index où insérer le repas
            index = -1
            drop_position = None

            # Si la liste des repas est vide, placer l'indicateur après les totaux
            if not self.repas_widgets:
                index = 0
                drop_position = QPoint(
                    0, self.separator.y() + self.separator.height() + 5
                )
            else:
                # Parcourir les widgets de repas pour trouver l'emplacement
                for i, repas_widget in enumerate(self.repas_widgets):
                    widget_top = repas_widget.y()
                    widget_bottom = widget_top + repas_widget.height()

                    # Si on est entre deux repas
                    if widget_top <= pos.y() <= widget_bottom:
                        # Si on est dans la moitié supérieure, insérer avant
                        if pos.y() < (widget_top + widget_bottom) / 2:
                            index = i
                            drop_position = QPoint(0, widget_top - 5)
                            break
                        # Si on est dans la moitié inférieure, insérer après
                        else:
                            index = i + 1
                            drop_position = QPoint(0, widget_bottom + 5)
                            break
                    # Si on est au-dessus du premier repas
                    elif pos.y() < widget_top and i == 0:
                        index = 0
                        drop_position = QPoint(0, widget_top - 5)
                        break

                # Si on n'a pas trouvé d'emplacement, c'est qu'on est après le dernier repas
                if index == -1:
                    index = len(self.repas_widgets)
                    last_widget = self.repas_widgets[-1]
                    drop_position = QPoint(
                        0, last_widget.y() + last_widget.height() + 5
                    )

            # Mettre à jour l'indicateur de drop
            self.drop_indicator_position = drop_position
            self.drop_index = index

            # Déclencher un repaint pour afficher l'indicateur
            self.update()

            event.acceptProposedAction()
        else:
            self.drop_indicator_position = None
            self.drop_index = -1
            event.ignore()

    def dragLeaveEvent(self, event):
        """Gère la sortie d'un drag de la zone du jour"""
        self.drop_indicator_position = None
        self.drop_index = -1
        self.update()
        super().dragLeaveEvent(event)

    def dragEndEvent(self, event):
        """Gère la fin d'une opération de drag (qu'elle réussisse ou non)"""
        # Réinitialiser l'indicateur de drop
        self.drop_indicator_position = None
        self.drop_index = -1
        self.update()

        super().dragEndEvent(event)

    def dropEvent(self, event):
        """Gère le drop d'un repas dans le jour"""
        if event.mimeData().hasFormat("application/x-repas"):
            # Récupérer les données du repas
            data = event.mimeData().data("application/x-repas").data().decode()
            repas_id, jour_origine = data.split("|")
            repas_id = int(repas_id)

            # Déterminer l'ordre du repas en fonction de l'indice de drop
            if self.drop_index >= 0:
                # Calculer l'ordre en fonction de l'index de drop et des repas existants
                if self.drop_index == 0:
                    # Premier élément, utiliser un ordre inférieur au premier repas actuel
                    if self.repas_widgets:
                        first_repas = self.repas_list[0]
                        ordre = max(1, first_repas.get("ordre", 1) - 1)
                    else:
                        ordre = 1
                elif self.drop_index >= len(self.repas_widgets):
                    # Dernier élément, utiliser un ordre supérieur au dernier repas
                    if self.repas_widgets:
                        last_repas = self.repas_list[-1]
                        ordre = last_repas.get("ordre", 1) + 1
                    else:
                        ordre = 1
                else:
                    # Entre deux repas, calculer l'ordre moyen
                    prev_repas = self.repas_list[self.drop_index - 1]
                    next_repas = self.repas_list[self.drop_index]
                    ordre = (
                        prev_repas.get("ordre", 1) + next_repas.get("ordre", 1)
                    ) / 2
            else:
                # Fallback: mettre en dernier
                ordre = len(self.repas_list) + 1

            # Mettre à jour le repas dans la base de données
            self.db_manager.changer_jour_repas(repas_id, self.jour, ordre)

            # Réinitialiser l'indicateur de drop
            self.drop_indicator_position = None
            self.drop_index = -1
            self.update()

            # Notifier que les repas ont été modifiés
            EVENT_BUS.repas_modifies.emit(self.semaine_id)

            # Recharger les données
            parent = self.parent()
            if parent and hasattr(parent, "load_data"):
                parent.load_data()

            event.acceptProposedAction()
        else:
            event.ignore()

    def paintEvent(self, event):
        """Surcharge pour dessiner l'indicateur de drop"""
        super().paintEvent(event)

        # Dessiner l'indicateur de drop si nécessaire
        if self.drop_indicator_position:
            painter = QPainter(self)
            pen = QPen(QColor(PRIMARY_COLOR))  # Couleur primaire
            pen.setWidth(3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)

            # Dessiner une ligne horizontale à la position de l'indicateur
            x1 = 10
            x2 = self.width() - 10
            y = self.drop_indicator_position.y()
            painter.drawLine(x1, y, x2, y)
