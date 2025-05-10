from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QFormLayout,
    QComboBox,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QPageLayout

from src.ui.dialogs.print_preview_dialog import PrintPreviewDialog
from src.utils.events import EVENT_BUS
from .tab_base import TabBase


class CoursesTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.current_semaine_id = None
        self.checkbox_states = self.db_manager.charger_etats_courses() or {}
        self.setup_ui()

        # Se connecter aux signaux du bus d'événements
        EVENT_BUS.semaine_ajoutee.connect(self.on_semaine_ajoutee)
        EVENT_BUS.semaine_supprimee.connect(self.on_semaine_supprimee)
        EVENT_BUS.semaines_modifiees.connect(self.refresh_data)

    def persist_checkbox_states(self):
        """Persiste les états des cases à cocher dans la base de données"""
        # Sauvegarder l'état actuel si nécessaire
        if self.tree.topLevelItemCount() > 0:
            self.save_checkbox_states()

        # Sauvegarder tous les états dans la base de données
        self.db_manager.sauvegarder_etats_courses(self.checkbox_states)

    def setup_ui(self):
        # Créer un layout principal sans marges pour le widget entier
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Créer un layout horizontal pour centrer le contenu
        center_layout = QHBoxLayout()

        # Créer un widget contenant le contenu réel avec sa largeur limitée
        content_widget = QWidget()
        content_widget.setMaximumWidth(900)
        content_widget.setMinimumWidth(700)

        # Layout principal du contenu
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Titre
        title = QLabel("<h1>Ma liste de courses</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Cette liste est générée à partir des repas planifiés pour la semaine."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc)

        # Description
        desc = QLabel(
            "Cette liste est générée à partir des repas planifiés pour la semaine.<br>"
            "<i>Astuce : Pour les repas déjà préparés ou à préparer en quantité multiple, "
            'utilisez le bouton "×1" sur la carte du repas.</i>'
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc)

        # Sélection de semaine et boutons dans la même section
        top_controls = QHBoxLayout()

        # Sélection de semaine (partie gauche)
        semaine_layout = QFormLayout()
        self.semaine_combo = QComboBox()
        self.semaine_combo.addItem("Toutes les semaines", None)
        self.semaine_combo.currentIndexChanged.connect(self.on_semaine_changed)
        semaine_layout.addRow("Semaine:", self.semaine_combo)

        # Ajouter la sélection de semaine à la partie gauche
        top_controls.addLayout(semaine_layout)

        # Ajouter un espacement extensible entre la sélection et les boutons
        top_controls.addStretch(1)

        # Boutons (partie droite)
        self.btn_select_all = QPushButton("Tout sélectionner")
        self.btn_select_all.clicked.connect(self.select_all_items)

        self.btn_deselect_all = QPushButton("Tout désélectionner")
        self.btn_deselect_all.clicked.connect(self.deselect_all_items)

        self.btn_refresh = QPushButton("Actualiser la liste")
        self.btn_refresh.clicked.connect(self.refresh_data)

        self.btn_print = QPushButton("Imprimer la sélection")
        self.btn_print.clicked.connect(self.print_liste_courses)

        # Ajouter les boutons à la partie droite
        top_controls.addWidget(self.btn_select_all)
        top_controls.addWidget(self.btn_deselect_all)
        top_controls.addWidget(self.btn_refresh)
        top_controls.addWidget(self.btn_print)

        # Ajouter cette section au layout principal
        main_layout.addLayout(top_controls)

        # Arbre pour afficher la liste de courses
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["À acheter", "Aliment", "Quantité", "Prix au kg"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Définir une hauteur minimale pour l'arbre
        self.tree.setMinimumHeight(400)
        main_layout.addWidget(self.tree)

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

        # Définir le layout pour ce widget
        self.setLayout(outer_layout)

        # Charger les semaines disponibles
        self.charger_semaines()

    def refresh_data(self):
        """Implémentation de la méthode de la classe de base pour actualiser les données"""
        # Sauvegarder l'état des cases à cocher avant l'actualisation
        if self.tree.topLevelItemCount() > 0:
            self.save_checkbox_states()
            self.persist_checkbox_states()  # Persister dans la BDD

        # Recharger les données
        self.charger_semaines()

    def charger_semaines(self):
        """Charge les semaines disponibles dans le sélecteur"""

        # Sauvegarder la semaine actuellement sélectionnée
        current_id = self.current_semaine_id

        # Bloquer temporairement le signal de changement
        self.semaine_combo.blockSignals(True)

        # Vider le combobox
        self.semaine_combo.clear()
        self.semaine_combo.addItem("Toutes les semaines", None)

        # Se connecter à la base de données et récupérer les semaines
        self.db_manager.connect()
        self.db_manager.cursor.execute(
            """
            SELECT DISTINCT r.semaine_id, s.nom_personnalise 
            FROM repas r
            LEFT JOIN semaines s ON r.semaine_id = s.id
            WHERE r.semaine_id IS NOT NULL
            ORDER BY r.semaine_id
            """
        )
        semaines = self.db_manager.cursor.fetchall()
        self.db_manager.disconnect()

        # Ajouter chaque semaine au combobox
        for semaine in semaines:
            semaine_id = semaine[0]
            semaine_nom = semaine[1] if semaine[1] else f"Semaine {semaine_id}"
            self.semaine_combo.addItem(semaine_nom, semaine_id)

        # Restaurer la sélection précédente si possible
        if current_id is not None:
            index = self.semaine_combo.findData(current_id)
            if index >= 0:
                self.semaine_combo.setCurrentIndex(index)
            else:
                # Si la semaine n'existe plus, revenir à "Toutes les semaines"
                self.current_semaine_id = None
                self.semaine_combo.setCurrentIndex(0)

        # Réactiver les signaux
        self.semaine_combo.blockSignals(False)

        # Charger les données avec la sélection courante
        self.load_data()

    def on_semaine_changed(self):
        """Appelé lorsqu'une semaine différente est sélectionnée"""
        # Sauvegarder l'état actuel avant de changer
        if self.tree.topLevelItemCount() > 0:
            self.save_checkbox_states()
            self.persist_checkbox_states()  # Persister dans la BDD

        self.current_semaine_id = self.semaine_combo.currentData()
        self.load_data()

    def load_data(self):
        """Charge les données de la liste de courses"""
        # Sauvegarder l'état des cases à cocher avant de vider l'arbre
        if self.current_semaine_id is not None:
            self.save_checkbox_states()

        self.tree.clear()

        # Récupérer la liste de courses pour la semaine sélectionnée
        liste_courses = self.db_manager.generer_liste_courses(self.current_semaine_id)

        total_aliments = 0
        for magasin, categories in liste_courses.items():
            magasin_count = 0
            for categorie, aliments in categories.items():
                magasin_count += len(aliments)
            total_aliments += magasin_count

        # Remplir l'arbre avec les données
        aliments_ajoutes = 0

        for magasin, categories in liste_courses.items():
            # Créer un élément pour le magasin
            magasin_item = QTreeWidgetItem(["", magasin, "", ""])
            magasin_item.setCheckState(0, Qt.Unchecked)
            magasin_item.setFlags(magasin_item.flags() | Qt.ItemIsAutoTristate)
            magasin_item.setExpanded(True)
            self.tree.addTopLevelItem(magasin_item)

            for categorie, aliments in categories.items():
                # Créer un élément pour la catégorie
                categorie_item = QTreeWidgetItem(["", categorie, "", ""])
                categorie_item.setCheckState(0, Qt.Unchecked)
                categorie_item.setFlags(categorie_item.flags() | Qt.ItemIsAutoTristate)
                categorie_item.setExpanded(True)
                magasin_item.addChild(categorie_item)

                for aliment in aliments:
                    # Afficher le prix au kilo
                    prix_au_kg = aliment["prix_kg"] or 0

                    # Identifier de façon unique cet aliment
                    aliment_id = f"{aliment['id']}"
                    aliments_ajoutes += 1

                    # Créer un élément pour l'aliment avec case à cocher
                    aliment_item = QTreeWidgetItem(
                        [
                            "",
                            f"{aliment['nom']} ({aliment['marque'] or 'Sans marque'})",
                            f"{aliment['quantite']}g",
                            f"{prix_au_kg:.2f} €/kg",
                        ]
                    )

                    # Stocker l'ID de l'aliment dans les données de l'item pour le retrouver plus tard
                    aliment_item.setData(0, Qt.UserRole, aliment_id)

                    # Restaurer l'état de la case à cocher si disponible, sinon cocher par défaut
                    check_state = self.get_checkbox_state(aliment_id)
                    if check_state is not None:
                        aliment_item.setCheckState(0, check_state)
                    else:
                        aliment_item.setCheckState(0, Qt.Checked)

                    categorie_item.addChild(aliment_item)

        # S'assurer que tous les éléments sont déployés
        self.tree.expandAll()

    def save_checkbox_states(self):
        """Sauvegarde l'état actuel des cases à cocher"""
        # Créer un dictionnaire pour cette semaine s'il n'existe pas déjà
        semaine_key = str(self.current_semaine_id) if self.current_semaine_id else "all"
        if semaine_key not in self.checkbox_states:
            self.checkbox_states[semaine_key] = {}

        # Parcourir tous les éléments d'aliments et sauvegarder leur état
        for i in range(self.tree.topLevelItemCount()):
            magasin_item = self.tree.topLevelItem(i)

            # Ignorer l'élément TOTAL s'il existe
            if magasin_item.text(1) == "TOTAL":
                continue

            for j in range(magasin_item.childCount()):
                categorie_item = magasin_item.child(j)

                for k in range(categorie_item.childCount()):
                    aliment_item = categorie_item.child(k)
                    aliment_id = aliment_item.data(0, Qt.UserRole)

                    # Sauvegarder l'état de la case (convertir en entier)
                    if aliment_id:
                        # Convertir CheckState en entier pour que SQLite puisse le stocker
                        # Utiliser la valeur numérique directement sans conversion avec int()
                        check_state = aliment_item.checkState(0)
                        if check_state == Qt.Checked:
                            state_value = 2  # Valeur correspondante à Qt.Checked
                        elif check_state == Qt.Unchecked:
                            state_value = 0  # Valeur correspondante à Qt.Unchecked
                        else:  # Qt.PartiallyChecked
                            state_value = (
                                1  # Valeur correspondante à Qt.PartiallyChecked
                            )

                        self.checkbox_states[semaine_key][aliment_id] = state_value

    def update_checkbox_states_from_saved(self):
        """Met à jour les états des cases à cocher à partir des états sauvegardés"""
        # Vérifier si le tree est vide
        if self.tree.topLevelItemCount() == 0:
            return

        # Identifier la clé de semaine actuelle
        semaine_key = str(self.current_semaine_id) if self.current_semaine_id else "all"

        # Vérifier s'il y a des états sauvegardés pour cette semaine
        if semaine_key not in self.checkbox_states:
            return

        saved_states = self.checkbox_states[semaine_key]

        # Parcourir tous les éléments d'aliments et restaurer leur état
        for i in range(self.tree.topLevelItemCount()):
            magasin_item = self.tree.topLevelItem(i)

            # Ignorer l'élément TOTAL s'il existe
            if magasin_item.text(1) == "TOTAL":
                continue

            for j in range(magasin_item.childCount()):
                categorie_item = magasin_item.child(j)

                for k in range(categorie_item.childCount()):
                    aliment_item = categorie_item.child(k)
                    aliment_id = aliment_item.data(0, Qt.UserRole)

                    # Restaurer l'état de la case si disponible
                    if aliment_id and aliment_id in saved_states:
                        # Convertir l'entier stocké en CheckState
                        state_value = saved_states[aliment_id]
                        if state_value == 2:
                            state = Qt.Checked
                        elif state_value == 0:
                            state = Qt.Unchecked
                        else:  # state_value == 1
                            state = Qt.PartiallyChecked

                        aliment_item.setCheckState(0, state)

        # Mettre à jour l'état des parents (catégories et magasins)
        for i in range(self.tree.topLevelItemCount()):
            magasin_item = self.tree.topLevelItem(i)
            if magasin_item.text(1) != "TOTAL":
                self._update_parent_check_state(magasin_item)

    def _update_parent_check_state(self, parent_item):
        """Met à jour l'état de la case à cocher d'un élément parent en fonction de ses enfants"""
        if parent_item.childCount() == 0:
            return

        # Compter les états des enfants
        checked_count = 0
        unchecked_count = 0

        for i in range(parent_item.childCount()):
            child = parent_item.child(i)

            # Mettre à jour l'état du parent si c'est un nœud interne
            if child.childCount() > 0:
                self._update_parent_check_state(child)

            # Compter l'état de l'enfant
            if child.checkState(0) == Qt.Checked:
                checked_count += 1
            elif child.checkState(0) == Qt.Unchecked:
                unchecked_count += 1

        # Définir l'état du parent
        if checked_count == parent_item.childCount():
            parent_item.setCheckState(0, Qt.Checked)
        elif unchecked_count == parent_item.childCount():
            parent_item.setCheckState(0, Qt.Unchecked)
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)

    def get_checkbox_state(self, aliment_id):
        """Récupère l'état d'une case à cocher pour un aliment donné"""
        semaine_key = str(self.current_semaine_id) if self.current_semaine_id else "all"

        # Vérifier si nous avons des états sauvegardés pour cette semaine
        if (
            semaine_key in self.checkbox_states
            and aliment_id in self.checkbox_states[semaine_key]
        ):
            # Convertir l'entier sauvegardé en Qt.CheckState
            state_value = self.checkbox_states[semaine_key][aliment_id]

            # Convertir en Qt.CheckState
            if state_value == 2:
                return Qt.Checked
            elif state_value == 0:
                return Qt.Unchecked
            else:  # state_value == 1
                return Qt.PartiallyChecked

        # Par défaut, retourner None (ce qui signifie "utiliser l'état par défaut")
        return None

    def on_tab_visible(self):
        """Méthode appelée quand l'onglet devient visible"""
        try:
            # Mettre à jour l'affichage en utilisant les états sauvegardés
            if hasattr(self, "tree") and self.tree.topLevelItemCount() > 0:
                self.update_checkbox_states_from_saved()
        except Exception as e:
            print(f"Erreur lors de l'actualisation des cases à cocher: {e}")

        # Appeler la méthode de la classe de base
        super().on_tab_visible()

    def on_tab_invisible(self):
        """Méthode appelée quand l'onglet devient invisible"""
        try:
            # Sauvegarder les états des cases à cocher
            if hasattr(self, "tree") and self.tree.topLevelItemCount() > 0:
                self.save_checkbox_states()
                self.persist_checkbox_states()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des cases à cocher: {e}")

        # Appeler la méthode de la classe de base
        super().on_tab_invisible()

    def select_all_items(self):
        """Sélectionne tous les éléments"""
        self._set_check_state_for_all(Qt.Checked)

    def deselect_all_items(self):
        """Désélectionne tous les éléments"""
        self._set_check_state_for_all(Qt.Unchecked)

    def _set_check_state_for_all(self, state):
        """Définit l'état de sélection pour tous les éléments"""
        for i in range(self.tree.topLevelItemCount()):
            magasin_item = self.tree.topLevelItem(i)

            # Ignorer l'élément TOTAL s'il existe
            if magasin_item.text(1) == "TOTAL":
                continue

            magasin_item.setCheckState(0, state)
            for j in range(magasin_item.childCount()):
                categorie_item = magasin_item.child(j)
                categorie_item.setCheckState(0, state)
                for k in range(categorie_item.childCount()):
                    aliment_item = categorie_item.child(k)
                    aliment_item.setCheckState(0, state)

        # Sauvegarder les états après avoir tout coché/décoché
        self.save_checkbox_states()
        self.persist_checkbox_states()

    def print_liste_courses(self):
        """Imprime la liste de courses formatée avec uniquement les éléments sélectionnés"""
        # Sauvegarder l'état actuel avant d'imprimer
        if self.tree.topLevelItemCount() > 0:
            self.save_checkbox_states()
            self.persist_checkbox_states()  # Persister dans la BDD

        # Créer un document HTML pour l'impression
        content = self.generate_print_content()

        # Afficher une boîte de dialogue d'aperçu avant impression
        preview_dialog = PrintPreviewDialog(content, self)
        if preview_dialog.exec():
            # Création d'une imprimante et configuration
            printer = QPrinter(QPrinter.HighResolution)

            # Configuration en format portrait (au lieu de paysage)
            layout = printer.pageLayout()
            layout.setOrientation(QPageLayout.Portrait)
            printer.setPageLayout(layout)

            # Afficher la boîte de dialogue d'impression
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec():
                # Créer et remplir un document texte
                document = QTextDocument()
                document.setHtml(content)

                # Imprimer le document
                document.print_(printer)

    def generate_print_content(self):
        """Génère le contenu HTML de la liste de courses pour l'impression sur une seule colonne"""
        html = "<html><head>"
        html += "<style>"
        html += "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; font-size: 14pt; }"
        html += "h1 { text-align: center; margin-bottom: 20px; font-size: 28pt; }"
        html += "h2 { margin-top: 20px; color: #2e7d32; font-size: 24pt; }"
        html += "h3 { margin-top: 10px; margin-left: 20px; font-size: 20pt; }"
        html += "ul { list-style-type: none; padding-left: 20px; margin-top: 10px; }"
        html += "li { margin: 5px 0; font-size: 10pt; line-height: 1.0; }"
        html += ".aliment { margin-left: 15px; }"
        html += (
            ".quantite { display: inline-block; min-width: 70px; font-weight: bold; }"
        )
        html += ".prix { color: #666; font-size: 14pt; margin-left: 10px; }"
        html += "</style>"
        html += "</head><body>"
        html += "<h1>Liste de courses</h1>"

        # Parcourir l'arbre pour trouver les éléments cochés
        for i in range(self.tree.topLevelItemCount()):
            magasin_item = self.tree.topLevelItem(i)
            magasin_nom = magasin_item.text(1)

            magasin_has_selected = False
            categories_html = ""

            for j in range(magasin_item.childCount()):
                categorie_item = magasin_item.child(j)
                categorie_nom = categorie_item.text(1)

                categorie_has_selected = False
                aliments_html = ""

                for k in range(categorie_item.childCount()):
                    aliment_item = categorie_item.child(k)
                    if aliment_item.checkState(0) == Qt.Checked:
                        categorie_has_selected = True
                        aliment_html = f"<li class='aliment'><span class='quantite'>{aliment_item.text(2)}</span> {aliment_item.text(1)} <span class='prix'>({aliment_item.text(3)})</span></li>"
                        aliments_html += aliment_html

                if categorie_has_selected:
                    magasin_has_selected = True
                    categories_html += (
                        f"<h3>{categorie_nom}</h3><ul>{aliments_html}</ul>"
                    )

            if magasin_has_selected:
                html += f"<h2>{magasin_nom}</h2>{categories_html}"

        html += "</body></html>"
        return html

    def on_semaine_ajoutee(self):
        """Appelé quand une semaine est ajoutée via le bus d'événements"""
        self.charger_semaines()

    def on_semaine_supprimee(self):
        """Appelé quand une semaine est supprimée via le bus d'événements"""
        self.charger_semaines()
