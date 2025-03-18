from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QMessageBox,
    QLineEdit,
    QInputDialog,
)
from PySide6.QtCore import Qt, Signal

from ..widgets.semaine_widget import SemaineWidget
from ..dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from ...utils.events import event_bus


class PlanningTab(QWidget):
    # Signaux pour notifier les changements de semaines
    semaine_supprimee = Signal(int)
    semaine_ajoutee = Signal(int)

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

        # Dictionnaire pour stocker les widgets des semaines
        self.semaines = {}

        # Compteur pour les nouvelles semaines
        self.semaine_counter = 1

        # Liste pour suivre les numéros de semaine utilisés
        self.semaine_ids = []

        # Dictionnaire pour stocker les noms personnalisés des onglets
        self.onglets_personnalises = {}

        # Dictionnaire pour les onglets {semaine_id: index}
        self.semaine_tabs = {}

        self.setup_ui()

        # Charger les semaines existantes avant d'ajouter une nouvelle
        semaines_chargees = self.charger_semaines_existantes()

        # Ajouter une semaine par défaut seulement si aucune n'a été chargée
        if not semaines_chargees:
            self.ajouter_semaine()  # Ajouter la première semaine par défaut

        # S'abonner aux événements de modification des aliments
        event_bus.aliment_supprime.connect(self.on_aliment_supprime)
        event_bus.aliments_modifies.connect(self.refresh_planning)

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Panel de contrôle des semaines
        control_layout = QHBoxLayout()

        self.btn_add_week = QPushButton("Ajouter une semaine")
        self.btn_add_week.clicked.connect(self.ajouter_semaine)
        control_layout.addWidget(self.btn_add_week)

        self.btn_remove_week = QPushButton("Supprimer la semaine courante")
        self.btn_remove_week.clicked.connect(self.supprimer_semaine_courante)
        control_layout.addWidget(self.btn_remove_week)

        # Ajout du bouton pour renommer la semaine courante
        self.btn_rename_week = QPushButton("Renommer la semaine courante")
        self.btn_rename_week.clicked.connect(self.renommer_semaine_courante)
        control_layout.addWidget(self.btn_rename_week)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Onglets pour les semaines
        self.tabs_semaines = QTabWidget()
        self.tabs_semaines.setTabsClosable(True)

        # Utiliser directement supprimer_onglet_semaine au lieu de fermer_semaine
        self.tabs_semaines.tabCloseRequested.connect(self.supprimer_onglet_semaine)
        self.tabs_semaines.currentChanged.connect(self.on_tab_changed)

        # Permettre le glisser-déposer des onglets
        self.tabs_semaines.setMovable(True)

        # Connecter le signal de déplacement d'onglet
        self.tabs_semaines.tabBar().tabMoved.connect(self.on_tab_moved)

        main_layout.addWidget(self.tabs_semaines, 1)

        # Suppression du bouton global pour ajouter un repas
        # Chaque jour a maintenant son propre bouton d'ajout

        self.setLayout(main_layout)

    def on_tab_changed(self, index):
        """Méthode appelée quand l'onglet actif change"""
        # Activer/désactiver les boutons en fonction de si un onglet est sélectionné
        has_tab = index >= 0
        self.btn_remove_week.setEnabled(has_tab)
        self.btn_rename_week.setEnabled(has_tab)
        # On ne modifie plus le bouton d'ajout global car il a été supprimé

    def on_tab_moved(self, from_index, to_index):
        """Méthode appelée lorsqu'un onglet est déplacé"""
        # Mettre à jour les noms d'onglets pour refléter l'ordre actuel
        self.mettre_a_jour_noms_onglets()

    def ajouter_semaine(self):
        """Ajoute une nouvelle semaine numérotée"""
        # Trouver le prochain numéro de semaine disponible
        semaine_id = 1

        # Si on a déjà des semaines, trouver le premier ID non utilisé
        if self.semaine_ids:
            # Trouver le premier numéro disponible dans la séquence
            for i in range(1, max(self.semaine_ids) + 2):
                if i not in self.semaine_ids:
                    semaine_id = i
                    break

        # Créer un widget pour cette semaine
        semaine_widget = SemaineWidget(self.db_manager, semaine_id)

        # Ajouter l'onglet
        # Plutôt que d'utiliser l'ID comme numéro, utiliser la position + 1
        position = self.tabs_semaines.count() + 1
        tab_text = f"Semaine {position}"
        index = self.tabs_semaines.addTab(semaine_widget, tab_text)

        # Stocker le widget dans le dictionnaire
        self.semaines[semaine_id] = semaine_widget

        # Ajouter l'ID à la liste des semaines utilisées
        self.semaine_ids.append(semaine_id)

        # Passer à cet onglet
        self.tabs_semaines.setCurrentIndex(index)

        # Mettre à jour l'état des boutons
        self.on_tab_changed(index)

        # Mettre à jour les noms d'onglets si nécessaire pour garantir la cohérence
        self.mettre_a_jour_noms_onglets()

        # Émettre les signaux pour notifier les autres composants
        self.semaine_ajoutee.emit(semaine_id)
        event_bus.semaine_ajoutee.emit(semaine_id)
        event_bus.semaines_modifiees.emit()

    def fermer_semaine(self, index):
        """Ferme une semaine à l'index donné"""
        # Si c'est la dernière semaine, ne pas permettre la fermeture
        if self.tabs_semaines.count() <= 1:
            QMessageBox.warning(
                self, "Impossible", "Vous devez garder au moins une semaine."
            )
            return

        # Utiliser la méthode supprimer_onglet_semaine pour assurer la suppression en DB
        self.supprimer_onglet_semaine(index)

    def supprimer_semaine_courante(self):
        """Supprime la semaine actuellement affichée"""
        current_index = self.tabs_semaines.currentIndex()
        self.fermer_semaine(current_index)

    def renommer_semaine_courante(self):
        """Ouvre un dialogue pour renommer la semaine courante"""
        current_index = self.tabs_semaines.currentIndex()
        if current_index < 0:
            return

        # Trouver l'ID de la semaine courante
        semaine_widget = self.tabs_semaines.widget(current_index)
        semaine_id = None
        for id, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = id
                break

        if semaine_id is not None:
            # Récupérer le nom actuel
            nom_actuel = self.tabs_semaines.tabText(current_index)

            # Ouvrir une boîte de dialogue pour saisir le nouveau nom
            (nouveau_nom, ok) = QInputDialog.getText(
                self,
                "Renommer la semaine",
                "Entrez un nouveau nom pour cette semaine:",
                QLineEdit.Normal,
                nom_actuel,
            )

            if ok and nouveau_nom:
                # Enregistrer le nouveau nom personnalisé
                self.onglets_personnalises[semaine_id] = nouveau_nom

                # Mettre à jour l'onglet
                self.tabs_semaines.setTabText(current_index, nouveau_nom)

    def mettre_a_jour_noms_onglets(self):
        """Met à jour les noms des onglets non personnalisés en fonction de leur position réelle"""
        position_counter = 1  # Compteur pour les onglets non personnalisés

        # Créer un mapping temporaire entre l'index d'onglet et l'ID de semaine
        index_to_id = {}
        for index in range(self.tabs_semaines.count()):
            semaine_widget = self.tabs_semaines.widget(index)
            for id, widget in self.semaines.items():
                if widget == semaine_widget:
                    index_to_id[index] = id
                    break

        # Mettre à jour les noms des onglets non personnalisés
        for index in range(self.tabs_semaines.count()):
            if index in index_to_id:
                semaine_id = index_to_id[index]
                if semaine_id not in self.onglets_personnalises:
                    # Onglet non personnalisé, utiliser la numérotation séquentielle
                    self.tabs_semaines.setTabText(index, f"Semaine {position_counter}")
                    position_counter += 1

    def ajouter_onglet_semaine(self, semaine_id, emit_signal=True):
        """Ajoute un nouvel onglet pour une semaine spécifique"""
        # Créer un widget de planning pour la semaine
        semaine_widget = SemainePlanningWidget(self.db_manager, semaine_id)

        # Ajouter l'onglet au TabWidget des semaines
        tab_index = self.semaines_tab_widget.addTab(
            semaine_widget, f"Semaine {semaine_id}"
        )

        # Garder une trace de cet onglet
        self.semaine_tabs[semaine_id] = tab_index

        # Émettre le signal si nécessaire
        if emit_signal:
            self.semaine_ajoutee.emit(semaine_id)

        return tab_index

    def ajouter_semaine_avec_id(self, semaine_id):
        """Ajoute une semaine avec un ID spécifique"""
        # Vérifier si cette semaine_id est déjà utilisée
        if semaine_id in self.semaine_ids:
            return False

        # Créer un widget pour cette semaine
        semaine_widget = SemaineWidget(self.db_manager, semaine_id)

        # Ajouter l'onglet
        tab_text = f"Semaine {semaine_id}"
        index = self.tabs_semaines.addTab(semaine_widget, tab_text)

        # Stocker le widget dans le dictionnaire
        self.semaines[semaine_id] = semaine_widget

        # Ajouter l'ID à la liste des semaines utilisées
        self.semaine_ids.append(semaine_id)

        # Stocker la relation entre semaine_id et index
        self.semaine_tabs[semaine_id] = index

        # Émettre le signal d'ajout
        self.semaine_ajoutee.emit(semaine_id)

        return True

    def charger_semaines_existantes(self):
        """Charge les semaines existantes depuis la base de données"""
        # Récupérer les IDs de semaines depuis le gestionnaire de DB
        semaines_ids = self.db_manager.get_semaines_existantes()

        # Si aucune semaine trouvée, retourner False
        if not semaines_ids:
            return False

        # Ajouter chaque semaine à l'interface
        for semaine in semaines_ids:
            semaine_id = semaine
            self.ajouter_semaine_avec_id(semaine_id)

        # Au moins une semaine a été chargée
        return True

    def supprimer_onglet_semaine(self, index):
        """Supprime un onglet de semaine"""
        # Si c'est la dernière semaine, ne pas permettre la fermeture
        if self.tabs_semaines.count() <= 1:
            QMessageBox.warning(
                self, "Impossible", "Vous devez garder au moins une semaine."
            )
            return

        # Trouver le semaine_id correspondant à cet index
        semaine_widget = self.tabs_semaines.widget(index)
        semaine_id = None

        # Rechercher l'ID de la semaine à partir du widget
        for sid, widget in self.semaines.items():
            if widget == semaine_widget:
                semaine_id = sid
                break

        if semaine_id is not None:
            print(
                f"Suppression de la semaine {semaine_id} de la base de données"
            )  # Log pour débugger

            # Supprimer de la base de données
            self.db_manager.supprimer_semaine(semaine_id)

            # Supprimer du dictionnaire des semaines
            del self.semaines[semaine_id]

            # Supprimer de la liste des IDs
            if semaine_id in self.semaine_ids:
                self.semaine_ids.remove(semaine_id)

            # Supprimer des onglets
            if semaine_id in self.semaine_tabs:
                del self.semaine_tabs[semaine_id]

            # Supprimer tout nom personnalisé pour cet onglet
            if semaine_id in self.onglets_personnalises:
                del self.onglets_personnalises[semaine_id]

            # Émettre les signaux
            self.semaine_supprimee.emit(semaine_id)
            # Émettre également sur le bus d'événements centralisé
            event_bus.semaine_supprimee.emit(semaine_id)
            event_bus.semaines_modifiees.emit()

        # Supprimer l'onglet visuellement
        self.tabs_semaines.removeTab(index)

        # Mettre à jour les noms d'onglets par défaut
        self.mettre_a_jour_noms_onglets()

    def on_aliment_supprime(self, aliment_id):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir tous les widgets de semaine
        self.refresh_planning()

    def refresh_planning(self):
        """Rafraîchit tous les widgets de semaine"""
        for semaine_id, widget in self.semaines.items():
            widget.load_data()
