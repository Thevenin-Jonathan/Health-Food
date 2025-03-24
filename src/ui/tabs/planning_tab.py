from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QLineEdit,
    QInputDialog,
    QTabBar,
)
from PySide6.QtCore import Signal, Qt, QTimer

from src.ui.widgets.semaine_widget import SemaineWidget
from src.ui.widgets.print_manager import PrintManager
from src.utils.events import EVENT_BUS


# Classe personnalisée pour le widget d'onglets afin de gérer le double-clic
class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_tab = parent

        # Installer un gestionnaire d'événements sur la barre d'onglets elle-même
        self.tabBar().installEventFilter(self)

        # Style pour le bouton d'ajout
        self.setStyleSheet(
            """
            QTabBar::tab:last {
                background-color: #f0f0f0;
                color: #333;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
            }
            QTabBar::tab:last:hover {
                background-color: #e0e0e0;
            }
        """
        )

    def eventFilter(self, obj, event):
        """Filtre les événements pour intercepter le double-clic sur la barre d'onglets"""
        if obj == self.tabBar() and event.type() == event.Type.MouseButtonDblClick:
            # Obtenir l'index de l'onglet cliqué directement à partir du tabBar
            pos = event.pos()
            index = self.tabBar().tabAt(pos)

            # Vérifier si l'index est valide et ce n'est pas le dernier onglet ("+")
            if index >= 0 and index < self.count() - 1:
                self.parent_tab.renommer_semaine(index)
                return True  # Événement traité

        # Dans tous les autres cas, laisser l'événement se propager
        return super().eventFilter(obj, event)

    # Supprimer ou garder inactive cette méthode qui ne semble pas fonctionner correctement
    def mouseDoubleClickEvent(self, event):
        # Nous utilisons désormais le filtre d'événements au lieu de cette méthode
        super().mouseDoubleClickEvent(event)


class PlanningTab(QWidget):
    # Signaux pour notifier les changements de semaines
    semaine_supprimee = Signal(int)
    semaine_ajoutee = Signal(int)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

        # Dictionnaire pour stocker les widgets des semaines
        self.semaines = {}

        # Liste pour suivre les numéros de semaine utilisés
        self.semaine_ids = []

        # Dictionnaire pour stocker les noms personnalisés des onglets
        self.onglets_personnalises = {}

        # Flags de contrôle
        self.add_in_progress = False
        self.first_load = True

        # Initialiser l'interface
        self.setup_ui()

        # Connecter les signaux
        self.tabs_semaines.tabBar().tabMoved.connect(self.on_tab_moved)

        # Charger les données de manière différée pour éviter les problèmes d'initialisation
        QTimer.singleShot(100, self.load_initial_data)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Panel de contrôle simplifié
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Widget d'onglets personnalisé
        self.tabs_semaines = CustomTabWidget(self)
        self.tabs_semaines.setTabsClosable(True)
        self.tabs_semaines.setMovable(True)
        self.tabs_semaines.currentChanged.connect(self.on_tab_changed)
        self.tabs_semaines.tabCloseRequested.connect(self.supprimer_onglet_semaine)

        # Créer un widget pour le coin supérieur droit du TabWidget
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(2)

        # Bouton d'impression dans le coin
        self.btn_print_planning = QPushButton("⎙ Imprimer")
        self.btn_print_planning.setFixedHeight(31)
        self.btn_print_planning.clicked.connect(self.imprimer_planning_courant)
        self.btn_print_planning.setEnabled(False)
        self.btn_print_planning.setStyleSheet("margin-right: 10px; margin-bottom: 6px;")
        corner_layout.addWidget(self.btn_print_planning)

        # Définir le widget de coin
        self.tabs_semaines.setCornerWidget(corner_widget, Qt.TopLeftCorner)

        main_layout.addWidget(self.tabs_semaines, 1)

    def load_initial_data(self):
        """Charge les données initiales (semaines existantes et onglet +)"""
        self.first_load = True

        # Charger les semaines existantes
        semaines_ids = self.db_manager.get_semaines_existantes()

        # Charger les noms personnalisés depuis la base de données
        self.onglets_personnalises = self.db_manager.get_noms_semaines()

        if semaines_ids:
            # Ajouter les semaines existantes
            for semaine_id in semaines_ids:
                self.ajouter_semaine_avec_id(semaine_id)
        else:
            # Aucune semaine existante, en créer une par défaut
            self.ajouter_semaine()

        # Ajouter l'onglet "+" à la fin
        self.ajouter_onglet_plus()

        # Mettre à jour les noms des onglets
        self.reorganiser_noms_onglets()

        # Se connecter aux événements
        EVENT_BUS.aliment_supprime.connect(self.on_aliment_supprime)
        EVENT_BUS.aliments_modifies.connect(self.refresh_data)

        self.first_load = False

    def ajouter_onglet_plus(self):
        """Ajoute un onglet "+" à la fin pour ajouter de nouvelles semaines"""
        # Créer un widget vide pour l'onglet +
        plus_widget = QWidget()

        # Ajouter l'onglet avec le symbole +
        plus_idx = self.tabs_semaines.addTab(plus_widget, "+")

        # Désactiver la fermeture pour cet onglet
        self.tabs_semaines.tabBar().setTabButton(plus_idx, QTabBar.RightSide, None)
        self.tabs_semaines.tabBar().setTabButton(plus_idx, QTabBar.LeftSide, None)

    def on_tab_changed(self, index):
        """Appelé quand un onglet est sélectionné"""
        # Si c'est l'onglet +, ajouter une nouvelle semaine
        if (
            index == self.tabs_semaines.count() - 1
            and not self.add_in_progress
            and not self.first_load
        ):
            self.add_in_progress = True

            # Ajouter une nouvelle semaine
            self.ajouter_semaine()

            self.add_in_progress = False

        # Activer/désactiver le bouton d'impression
        has_tab = index >= 0 and index < self.tabs_semaines.count() - 1
        self.btn_print_planning.setEnabled(has_tab)

    def on_tab_moved(self, from_index, to_index):
        """Assure que l'onglet + reste toujours à la fin"""
        count = self.tabs_semaines.count()

        # Si c'est l'onglet + qui a été déplacé, le remettre à la fin
        if from_index == count - 1 and to_index != count - 1:
            self.tabs_semaines.tabBar().moveTab(to_index, count - 1)
            return

        # Si d'autres onglets ont été déplacés, mettre à jour les noms
        self.reorganiser_noms_onglets()

    def reorganiser_noms_onglets(self):
        """Met à jour les noms des onglets pour assurer la cohérence"""
        # Ignorer l'onglet "+"
        tab_count = self.tabs_semaines.count() - 1

        # Vérifier la validité
        if tab_count <= 0:
            return

        # Pour chaque onglet (sauf le "+"), mettre à jour son nom
        for i in range(tab_count):
            # Récupérer le widget et trouver l'ID correspondant
            widget = self.tabs_semaines.widget(i)
            semaine_id = None

            for sid, w in self.semaines.items():
                if w == widget:
                    semaine_id = sid
                    break

            if semaine_id is not None:
                # Utiliser le nom personnalisé s'il existe
                if semaine_id in self.onglets_personnalises:
                    nom = self.onglets_personnalises[semaine_id]
                else:
                    # Sinon, utiliser "Semaine X" avec X = position + 1
                    nom = f"Semaine {i + 1}"

                # Mettre à jour le texte de l'onglet
                self.tabs_semaines.setTabText(i, nom)

    def ajouter_semaine(self):
        """Ajoute une nouvelle semaine et son onglet"""
        # Trouver le prochain ID de semaine disponible
        semaine_id = 1
        if self.semaine_ids:
            for i in range(1, max(self.semaine_ids) + 2):
                if i not in self.semaine_ids:
                    semaine_id = i
                    break

        # Créer le widget de semaine
        semaine_widget = SemaineWidget(self.db_manager, semaine_id)

        # Position: juste avant l'onglet + (dernier)
        position = self.tabs_semaines.count() - 1

        # Ajouter l'onglet avec un nom temporaire
        index = self.tabs_semaines.insertTab(
            position, semaine_widget, f"Semaine {position + 1}"
        )

        # Stocker les références
        self.semaines[semaine_id] = semaine_widget
        self.semaine_ids.append(semaine_id)

        # Sélectionner le nouvel onglet
        self.tabs_semaines.setCurrentIndex(index)

        # Mettre à jour les noms des onglets
        self.reorganiser_noms_onglets()

        # Notifier les autres composants
        self.semaine_ajoutee.emit(semaine_id)
        EVENT_BUS.semaine_ajoutee.emit(semaine_id)
        EVENT_BUS.semaines_modifiees.emit()

        return semaine_id

    def ajouter_semaine_avec_id(self, semaine_id):
        """Ajoute une semaine existante avec un ID spécifique"""
        # Vérifier si la semaine existe déjà
        if semaine_id in self.semaine_ids:
            return False

        # Créer le widget de semaine
        semaine_widget = SemaineWidget(self.db_manager, semaine_id)

        # Ajouter l'onglet à la fin (avant l'onglet + s'il existe)
        position = self.tabs_semaines.count()

        # Nom temporaire qui sera mis à jour par reorganiser_noms_onglets
        index = self.tabs_semaines.insertTab(
            position, semaine_widget, f"Semaine {semaine_id}"
        )

        # Stocker les références
        self.semaines[semaine_id] = semaine_widget
        self.semaine_ids.append(semaine_id)

        return True

    def renommer_semaine(self, index):
        """Renomme un onglet de semaine"""
        if index < 0 or index >= self.tabs_semaines.count() - 1:
            return

        # Trouver le widget et l'ID de semaine
        semaine_widget = self.tabs_semaines.widget(index)
        semaine_id = None

        for sid, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = sid
                break

        if semaine_id is None:
            return

        # Récupérer le nom actuel
        nom_actuel = self.tabs_semaines.tabText(index)

        # Demander le nouveau nom
        nouveau_nom, ok = QInputDialog.getText(
            self, "Renommer la semaine", "Nouveau nom:", QLineEdit.Normal, nom_actuel
        )

        if ok and nouveau_nom:
            # Mettre à jour le nom personnalisé
            self.onglets_personnalises[semaine_id] = nouveau_nom
            self.tabs_semaines.setTabText(index, nouveau_nom)

            # Sauvegarder le nom en base de données
            self.db_manager.sauvegarder_nom_semaine(semaine_id, nouveau_nom)

    def supprimer_onglet_semaine(self, index):
        """Supprime un onglet de semaine"""
        # Effectuer les vérifications de base
        if index == self.tabs_semaines.count() - 1:  # Ne pas fermer l'onglet +
            return

        if self.tabs_semaines.count() <= 2:  # Garder au moins une semaine
            QMessageBox.warning(
                self, "Impossible", "Vous devez conserver au moins une semaine."
            )
            return

        # Obtenir les informations avant de supprimer quoi que ce soit
        semaine_widget = self.tabs_semaines.widget(index)
        if not semaine_widget:
            return

        # Rechercher l'ID de la semaine correspondante
        semaine_id = None
        for sid, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = sid
                break

        if not semaine_id:
            return

        # Déterminer l'index à sélectionner après la suppression
        current_index = self.tabs_semaines.currentIndex()
        is_active_tab = index == current_index

        # Supprimer la semaine de la base de données
        try:
            self.db_manager.supprimer_semaine(semaine_id)
        except Exception as e:
            print(f"Erreur lors de la suppression de la semaine {semaine_id}: {e}")
        finally:
            # Supprimer également le nom personnalisé de la semaine
            try:
                self.db_manager.supprimer_nom_semaine(semaine_id)
            except Exception as e:
                print(
                    f"Erreur lors de la suppression du nom personnalisé de la semaine {semaine_id}: {e}"
                )

        # Supprimer des collections internes
        try:
            del self.semaines[semaine_id]
            if semaine_id in self.semaine_ids:
                self.semaine_ids.remove(semaine_id)
            if semaine_id in self.onglets_personnalises:
                del self.onglets_personnalises[semaine_id]
        except Exception as e:
            print(
                f"Erreur lors de la suppression de la semaine {semaine_id} des collections: {e}"
            )

        # Émettre les signaux de notification
        self.semaine_supprimee.emit(semaine_id)
        EVENT_BUS.semaine_supprimee.emit(semaine_id)
        EVENT_BUS.semaines_modifiees.emit()

        # Déterminer le nouvel onglet à sélectionner avant de supprimer l'onglet actuel
        if is_active_tab:
            # Si on ferme l'onglet actif, prendre le précédent s'il existe
            if index > 0:
                new_index = index - 1
            else:
                # Si c'est le premier, prendre le suivant (qui deviendra le premier)
                new_index = 0
        else:
            # Si on ne ferme pas l'onglet actif, garder la même sélection
            # mais ajuster si l'index actuel est après celui qu'on supprime
            new_index = current_index
            if current_index > index:
                new_index -= 1

        # Supprimer l'onglet du TabWidget
        try:
            self.tabs_semaines.blockSignals(
                True
            )  # Bloquer les signaux pendant la suppression
            self.tabs_semaines.removeTab(index)
            self.tabs_semaines.blockSignals(False)  # Réactiver les signaux
        except Exception as e:
            print(f"Erreur lors de la suppression de l'onglet: {e}")
            self.tabs_semaines.blockSignals(
                False
            )  # S'assurer que les signaux sont réactivés

        # Appliquer la nouvelle sélection si le TabWidget a encore des onglets
        if self.tabs_semaines.count() > 1:  # Au moins un onglet + le "+"
            # Vérifier que l'index est dans les limites et n'est pas le "+"
            max_valid_index = self.tabs_semaines.count() - 2
            new_index = min(max_valid_index, new_index)
            new_index = max(0, new_index)

            QTimer.singleShot(
                10, lambda idx=new_index: self.tabs_semaines.setCurrentIndex(idx)
            )

        # Mettre à jour les noms d'onglets
        QTimer.singleShot(20, self.reorganiser_noms_onglets)

    def imprimer_planning_courant(self):
        """Imprime le planning de la semaine courante"""
        current_index = self.tabs_semaines.currentIndex()

        if current_index < 0 or current_index >= self.tabs_semaines.count() - 1:
            return

        # Trouver l'ID de semaine
        semaine_widget = self.tabs_semaines.widget(current_index)
        semaine_id = None

        for sid, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = sid
                break

        if semaine_id is not None:
            print_manager = PrintManager(self.db_manager)
            print_manager.print_planning(semaine_id)

    def on_aliment_supprime(self):
        """Appelé quand un aliment est supprimé"""
        self.refresh_data()

    def refresh_data(self):
        """Rafraîchit tous les widgets de semaine"""
        for semaine in self.semaines.values():
            semaine.load_data()
