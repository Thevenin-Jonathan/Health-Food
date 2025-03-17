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
)
from PySide6.QtCore import Qt
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QPageLayout

from .tab_base import TabBase
from ..dialogs.print_preview_dialog import PrintPreviewDialog
from ...utils.events import event_bus
from ...utils.config import JOURS_SEMAINE


class CoursesTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.current_semaine_id = None
        self.setup_ui()

        # Se connecter aux signaux du bus d'événements
        event_bus.semaine_ajoutee.connect(self.on_semaine_ajoutee)
        event_bus.semaine_supprimee.connect(self.on_semaine_supprimee)
        event_bus.semaines_modifiees.connect(self.refresh_data)

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Titre
        title = QLabel("<h1>Liste de courses</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Cette liste est générée à partir des repas planifiés pour la semaine."
        )
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Sélection de semaine
        semaine_layout = QFormLayout()
        self.semaine_combo = QComboBox()
        self.semaine_combo.addItem("Toutes les semaines", None)
        self.semaine_combo.currentIndexChanged.connect(self.on_semaine_changed)
        semaine_layout.addRow("Semaine:", self.semaine_combo)
        main_layout.addLayout(semaine_layout)

        # Arbre pour afficher la liste de courses
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["À acheter", "Aliment", "Quantité", "Prix au kg"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.tree)

        # Boutons
        buttons_layout = QHBoxLayout()

        self.btn_select_all = QPushButton("Tout sélectionner")
        self.btn_select_all.clicked.connect(self.select_all_items)

        self.btn_deselect_all = QPushButton("Tout désélectionner")
        self.btn_deselect_all.clicked.connect(self.deselect_all_items)

        self.btn_refresh = QPushButton("Actualiser la liste")
        self.btn_refresh.clicked.connect(self.refresh_data)

        self.btn_print = QPushButton("Imprimer la sélection")
        self.btn_print.clicked.connect(self.print_liste_courses)

        buttons_layout.addWidget(self.btn_select_all)
        buttons_layout.addWidget(self.btn_deselect_all)
        buttons_layout.addWidget(self.btn_refresh)
        buttons_layout.addWidget(self.btn_print)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Charger les semaines disponibles
        self.charger_semaines()

    def refresh_data(self):
        """Implémentation de la méthode de la classe de base pour actualiser les données"""
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
            SELECT DISTINCT semaine_id FROM repas
            WHERE semaine_id IS NOT NULL
            ORDER BY semaine_id
            """
        )
        semaines = self.db_manager.cursor.fetchall()
        self.db_manager.disconnect()

        # Ajouter chaque semaine au combobox
        for semaine in semaines:
            semaine_id = semaine[0]
            self.semaine_combo.addItem(f"Semaine {semaine_id}", semaine_id)

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

    def on_semaine_changed(self, index):
        """Appelé lorsqu'une semaine différente est sélectionnée"""
        self.current_semaine_id = self.semaine_combo.currentData()
        self.load_data()

    def load_data(self):
        """Charge les données de la liste de courses"""
        self.tree.clear()

        # Récupérer la liste de courses pour la semaine sélectionnée
        liste_courses = self.db_manager.generer_liste_courses(self.current_semaine_id)

        # Remplir l'arbre avec les données
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

                    # Créer un élément pour l'aliment avec case à cocher
                    aliment_item = QTreeWidgetItem(
                        [
                            "",
                            f"{aliment['nom']} ({aliment['marque'] or 'Sans marque'})",
                            f"{aliment['quantite']}g",
                            f"{prix_au_kg:.2f} €/kg",
                        ]
                    )
                    aliment_item.setCheckState(0, Qt.Checked)  # Coché par défaut
                    categorie_item.addChild(aliment_item)

        # S'assurer que tous les éléments sont déployés
        self.tree.expandAll()

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

    def print_liste_courses(self):
        """Imprime la liste de courses formatée avec uniquement les éléments sélectionnés"""
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

    def on_semaine_ajoutee(self, semaine_id):
        """Appelé quand une semaine est ajoutée via le bus d'événements"""
        self.charger_semaines()

    def on_semaine_supprimee(self, semaine_id):
        """Appelé quand une semaine est supprimée via le bus d'événements"""
        self.charger_semaines()
