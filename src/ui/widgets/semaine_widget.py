from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QLabel,
    QFrame,
    QGridLayout,
    QMessageBox,
    QProgressBar,
    QStyle,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QTextDocument, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from ..dialogs.repas_dialog import RepasDialog
from ..dialogs.aliment_repas_dialog import AlimentRepasDialog
from ..dialogs.remplacer_repas_dialog import RemplacerRepasDialog
from ..dialogs.print_preview_dialog import PrintPreviewDialog
from ...utils.events import event_bus
from ...utils.config import JOURS_SEMAINE, BUTTON_STYLES


class SemaineWidget(QWidget):
    """Widget représentant une semaine de planning"""

    def __init__(self, db_manager, semaine_id):
        super().__init__()
        self.db_manager = db_manager
        self.semaine_id = semaine_id  # Identifiant numérique de la semaine

        # Charger les objectifs utilisateur dès l'initialisation
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()

        self.setup_ui()
        self.load_data()

        # S'abonner aux événements
        event_bus.aliment_supprime.connect(self.on_aliment_supprime)
        if hasattr(event_bus, "utilisateur_modifie"):
            event_bus.utilisateur_modifie.connect(self.update_objectifs_utilisateur)

    def charger_objectifs_utilisateur(self):
        """Récupère les objectifs nutritionnels de l'utilisateur"""
        user_data = self.db_manager.get_utilisateur()
        return {
            "calories": user_data.get("objectif_calories", 2500),
            "proteines": user_data.get("objectif_proteines", 180),
            "glucides": user_data.get("objectif_glucides", 250),
            "lipides": user_data.get("objectif_lipides", 70),
        }

    def update_objectifs_utilisateur(self):
        """Met à jour les objectifs quand le profil utilisateur est modifié"""
        self.objectifs_utilisateur = self.charger_objectifs_utilisateur()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Bouton pour imprimer le planning
        print_layout = QHBoxLayout()
        self.btn_print = QPushButton("Imprimer le planning")
        # Utiliser une icône standard disponible
        self.btn_print.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
        )
        self.btn_print.clicked.connect(self.print_planning)
        print_layout.addStretch()
        print_layout.addWidget(self.btn_print)
        main_layout.addLayout(print_layout)

        # Conteneur pour les jours avec scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget contenant les jours
        self.days_container = QWidget()
        self.days_layout = QGridLayout()

        # Définir une largeur maximum pour les colonnes des jours
        self.days_layout.setColumnMinimumWidth(0, 300)  # Largeur minimum
        self.days_layout.setColumnStretch(0, 1)  # Facteur d'étirement

        self.days_container.setLayout(self.days_layout)

        self.scroll_area.setWidget(self.days_container)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

    def load_data(self):
        # Nettoyer la disposition existante
        while self.days_layout.count():
            item = self.days_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Récupérer les données des repas pour la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)

        for col, jour in enumerate(JOURS_SEMAINE):
            # Créer un widget pour le jour
            day_widget = QWidget()
            day_widget.setMaximumWidth(350)
            day_layout = QVBoxLayout()
            day_widget.setLayout(day_layout)

            # Titre du jour avec bouton d'ajout
            jour_header = QHBoxLayout()
            titre_jour = QLabel(f"<h2>{jour}</h2>")
            jour_header.addWidget(titre_jour)

            # Bouton pour ajouter un repas à ce jour
            btn_add_day = QPushButton("+")
            btn_add_day.setFixedSize(30, 30)
            btn_add_day.setStyleSheet(BUTTON_STYLES["add"])
            btn_add_day.setToolTip(f"Ajouter un repas le {jour}")
            btn_add_day.clicked.connect(lambda checked, j=jour: self.add_meal(j))
            jour_header.addWidget(btn_add_day)

            day_layout.addLayout(jour_header)

            # Ajouter les repas du jour
            total_cal = 0
            total_prot = 0
            total_gluc = 0
            total_lip = 0

            for repas in repas_semaine[jour]:
                # Créer un widget pour le repas
                repas_widget = QFrame()
                repas_widget.setFrameShape(QFrame.StyledPanel)
                repas_widget.setFrameShadow(QFrame.Raised)
                repas_layout = QVBoxLayout()
                repas_widget.setLayout(repas_layout)

                # Titre du repas avec boutons
                repas_header = QHBoxLayout()
                repas_title = QLabel(f"<h3>{repas['nom']}</h3>")
                repas_header.addWidget(repas_title)
                repas_header.addStretch()  # Ajouter un espace extensible pour pousser les boutons à droite

                # Bouton pour ajouter des aliments
                btn_add = QPushButton("+")
                btn_add.setFixedSize(24, 24)  # Taille fixe pour cohérence
                btn_add.setStyleSheet(BUTTON_STYLES["add"])
                btn_add.setToolTip("Ajouter un aliment à ce repas")
                btn_add.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.add_food_to_meal(r_id)
                )

                # Bouton pour remplacer le repas par une recette
                btn_replace = QPushButton("⇄")
                btn_replace.setFixedSize(24, 24)
                btn_replace.setStyleSheet(BUTTON_STYLES["replace"])
                btn_replace.setToolTip("Remplacer par une recette")
                btn_replace.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.remplacer_repas_par_recette(
                        r_id
                    )
                )

                # Bouton pour supprimer le repas (croix rouge simplifiée)
                btn_delete = QPushButton("×")
                btn_delete.setFixedSize(24, 24)
                btn_delete.setStyleSheet(BUTTON_STYLES["delete"])
                btn_delete.setToolTip("Supprimer ce repas")
                btn_delete.clicked.connect(
                    lambda checked, r_id=repas["id"]: self.delete_meal(r_id)
                )

                # Ajouter les boutons directement au layout sans conteneurs supplémentaires
                repas_header.addWidget(btn_add)
                repas_header.addWidget(btn_replace)
                repas_header.addWidget(btn_delete)
                repas_layout.addLayout(repas_header)

                # Ajouter les aliments du repas
                if repas["aliments"]:
                    for aliment in repas["aliments"]:
                        alim_layout = QHBoxLayout()

                        # Texte de base de l'aliment
                        alim_text = f"{aliment['nom']} ({aliment['quantite']}g) - {aliment['calories'] * aliment['quantite'] / 100:.0f} kcal"
                        alim_label = QLabel(alim_text)
                        alim_label.setWordWrap(True)
                        alim_layout.addWidget(alim_label)
                        alim_layout.addStretch()  # Ajouter un espace extensible

                        # Ajouter un tooltip avec les informations détaillées des macros
                        # Calculer les valeurs nutritionnelles en fonction du poids
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

                        # Bouton pour supprimer l'aliment (croix rouge simplifiée)
                        btn_remove = QPushButton("×")
                        btn_remove.setFixedSize(20, 20)  # Plus petit pour les aliments
                        btn_remove.setStyleSheet(BUTTON_STYLES["delete"])
                        btn_remove.setToolTip("Supprimer cet aliment")
                        btn_remove.clicked.connect(
                            lambda checked, r_id=repas["id"], a_id=aliment[
                                "id"
                            ]: self.remove_food_from_meal(r_id, a_id)
                        )

                        # Ajouter le bouton directement sans conteneur
                        alim_layout.addWidget(btn_remove)

                        repas_layout.addLayout(alim_layout)
                else:
                    repas_layout.addWidget(QLabel("Aucun aliment"))

                # Afficher les totaux du repas
                repas_layout.addWidget(
                    QLabel(
                        f"<b>Total:</b> {repas['total_calories']:.0f} kcal | "
                        f"P: {repas['total_proteines']:.1f}g | "
                        f"G: {repas['total_glucides']:.1f}g | "
                        f"L: {repas['total_lipides']:.1f}g"
                    )
                )

                day_layout.addWidget(repas_widget)

                # Ajouter aux totaux du jour
                total_cal += repas["total_calories"]
                total_prot += repas["total_proteines"]
                total_gluc += repas["total_glucides"]
                total_lip += repas["total_lipides"]

            # Afficher les totaux du jour
            total_widget = QFrame()
            total_widget.setFrameShape(QFrame.StyledPanel)
            total_widget.setProperty("class", "day-total")
            total_layout = QVBoxLayout()
            total_widget.setLayout(total_layout)

            total_layout.addWidget(QLabel(f"<h3>Total du jour</h3>"))

            # Créer un widget pour chaque ligne de macro avec barre de progression
            objectifs = self.objectifs_utilisateur

            # Calories
            cal_layout = QHBoxLayout()
            cal_text = QLabel(f"<b>Calories:</b> {total_cal:.0f}")
            cal_layout.addWidget(cal_text)

            # Pourcentage de l'objectif
            pct_cal = (
                int((total_cal / objectifs["calories"]) * 100)
                if objectifs["calories"] > 0
                else 0
            )
            cal_obj_text = QLabel(f"/ {objectifs['calories']} ({pct_cal}%)")
            cal_layout.addWidget(cal_obj_text)

            # Ajouter le layout au layout total
            total_layout.addLayout(cal_layout)

            # Ajouter la barre de progression en arrière-plan
            cal_progress = self.create_background_progress_bar(
                total_cal, objectifs["calories"]
            )
            total_layout.addWidget(cal_progress)

            # Protéines
            prot_layout = QHBoxLayout()
            prot_text = QLabel(f"<b>Protéines:</b> {total_prot:.1f}g")
            prot_layout.addWidget(prot_text)

            # Pourcentage de l'objectif
            pct_prot = (
                int((total_prot / objectifs["proteines"]) * 100)
                if objectifs["proteines"] > 0
                else 0
            )
            prot_obj_text = QLabel(f"/ {objectifs['proteines']}g ({pct_prot}%)")
            prot_layout.addWidget(prot_obj_text)

            # Ajouter le layout au layout total
            total_layout.addLayout(prot_layout)

            # Ajouter la barre de progression en arrière-plan
            prot_progress = self.create_background_progress_bar(
                total_prot, objectifs["proteines"]
            )
            total_layout.addWidget(prot_progress)

            # Glucides
            gluc_layout = QHBoxLayout()
            gluc_text = QLabel(f"<b>Glucides:</b> {total_gluc:.1f}g")
            gluc_layout.addWidget(gluc_text)

            # Pourcentage de l'objectif
            pct_gluc = (
                int((total_gluc / objectifs["glucides"]) * 100)
                if objectifs["glucides"] > 0
                else 0
            )
            gluc_obj_text = QLabel(f"/ {objectifs['glucides']}g ({pct_gluc}%)")
            gluc_layout.addWidget(gluc_obj_text)

            # Ajouter le layout au layout total
            total_layout.addLayout(gluc_layout)

            # Ajouter la barre de progression en arrière-plan
            gluc_progress = self.create_background_progress_bar(
                total_gluc, objectifs["glucides"]
            )
            total_layout.addWidget(gluc_progress)

            # Lipides
            lip_layout = QHBoxLayout()
            lip_text = QLabel(f"<b>Lipides:</b> {total_lip:.1f}g")
            lip_layout.addWidget(lip_text)

            # Pourcentage de l'objectif
            pct_lip = (
                int((total_lip / objectifs["lipides"]) * 100)
                if objectifs["lipides"] > 0
                else 0
            )
            lip_obj_text = QLabel(f"/ {objectifs['lipides']}g ({pct_lip}%)")
            lip_layout.addWidget(lip_obj_text)

            # Ajouter le layout au layout total
            total_layout.addLayout(lip_layout)

            # Ajouter la barre de progression en arrière-plan
            lip_progress = self.create_background_progress_bar(
                total_lip, objectifs["lipides"]
            )
            total_layout.addWidget(lip_progress)

            day_layout.addWidget(total_widget)
            day_layout.addStretch()

            self.days_layout.addWidget(day_widget, 0, col)

        # Ajouter ce code ici, après la boucle qui crée les colonnes
        for col in range(7):  # Pour chaque jour
            self.days_layout.setColumnStretch(col, 1)  # Répartition égale

    def create_background_progress_bar(self, value, max_value):
        """Crée une barre de progression simplifiée pour l'arrière-plan"""
        progress = QProgressBar()
        progress.setMinimum(0)

        # Pour l'affichage visuel de la barre, étendre le maximum si nécessaire()
        if value > max_value:
            progress.setMaximum(int(value * 1.1))
        else:
            progress.setMaximum(max_value)

        progress.setValue(value)
        progress.setTextVisible(False)  # Pas de texte, juste la barre

        # Hauteur minimale pour la barre
        progress.setFixedHeight(10)

        # Colorer la barre selon le pourcentage
        palette = QPalette()
        if value < max_value * 0.8:
            palette.setColor(QPalette.Highlight, QColor("orange"))  # En dessous
        elif value <= max_value * 1.05:
            palette.setColor(
                QPalette.Highlight, QColor("#4CAF50")
            )  # Dans la cible (vert)
        else:
            palette.setColor(QPalette.Highlight, QColor("#F44336"))  # Au-dessus (rouge)

        progress.setPalette(palette)

        # Appliquer un style pour une barre plus discrète
        progress.setStyleSheet(
            """
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                margin: 2px 0px;
            }
        """
        )

        return progress

    def add_meal(self, jour=None):
        """Ajoute un repas à cette semaine, avec jour optionnel prédéfini"""
        dialog = RepasDialog(
            self, self.db_manager, self.semaine_id, jour_predefini=jour
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

            self.load_data()

    def add_food_to_meal(self, repas_id):
        dialog = AlimentRepasDialog(self, self.db_manager)
        if dialog.exec():
            aliment_id, quantite = dialog.get_data()
            self.db_manager.ajouter_aliment_repas(repas_id, aliment_id, quantite)
            self.load_data()

    def delete_meal(self, repas_id):
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_repas(repas_id)
            self.load_data()

    def remove_food_from_meal(self, repas_id, aliment_id):
        """Supprimer un aliment d'un repas"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet aliment du repas ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db_manager.supprimer_aliment_repas(repas_id, aliment_id)
            self.load_data()

    def remplacer_repas_par_recette(self, repas_id):
        """Remplace un repas existant par une recette avec prévisualisation des différences"""
        # Récupérer les informations du repas actuel
        repas_actuel = None
        for jour, repas_list in self.db_manager.get_repas_semaine(
            self.semaine_id
        ).items():
            for repas in repas_list:
                if repas["id"] == repas_id:
                    repas_actuel = repas
                    break
            if repas_actuel:
                break

        if not repas_actuel:
            return

        # Ouvrir le dialogue de comparaison et remplacement
        dialog = RemplacerRepasDialog(self, self.db_manager, repas_actuel)
        if dialog.exec():
            recette_id, facteurs_ou_ingredients = dialog.get_data()

            # Supprimer l'ancien repas
            self.db_manager.supprimer_repas(repas_id)

            if recette_id == "personnalisee":
                # Traiter le cas d'une recette personnalisée (où des ingrédients ont été ajoutés/supprimés)
                self.db_manager.appliquer_recette_modifiee_au_jour(
                    dialog.recette_courante_id,  # ID de la recette de base
                    facteurs_ou_ingredients,  # Liste des ingrédients avec quantités ajustées
                    repas_actuel["jour"],
                    repas_actuel["ordre"],
                    self.semaine_id,
                )
            else:
                # Créer un nouveau repas basé sur la recette avec les quantités ajustées
                self.db_manager.appliquer_repas_type_au_jour_avec_facteurs(
                    recette_id,
                    repas_actuel["jour"],
                    repas_actuel["ordre"],
                    self.semaine_id,
                    facteurs_ou_ingredients,
                )

            # Actualiser l'affichage
            self.load_data()

    def print_planning(self):
        """Imprime le planning de la semaine actuelle"""
        # Générer le contenu HTML pour l'impression
        content = self.generate_print_content()

        # Afficher une boîte de dialogue d'aperçu avant impression
        preview_dialog = PrintPreviewDialog(content, self)
        if preview_dialog.exec():
            # Création d'une imprimante et configuration
            printer = QPrinter(QPrinter.HighResolution)

            # Configuration en format paysage pour avoir tous les jours sur une seule page
            printer.setPageOrientation(QPageLayout.Landscape)

            # Afficher la boîte de dialogue d'impression
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec():
                # Créer et remplir un document texte
                document = QTextDocument()

                # Désactiver les marges internes du document
                document.setDocumentMargin(0)

                # Charger le contenu HTML
                document.setHtml(content)

                # Imprimer le document
                document.print_(printer)

    def generate_print_content(self):
        """Génère le contenu HTML du planning pour l'impression - version optimisée"""
        # Récupérer les données de la semaine
        repas_semaine = self.db_manager.get_repas_semaine(self.semaine_id)
        jours = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]

        # Créer le document HTML avec un style optimisé pour l'impression
        html = "<html><head>"
        html += "<meta charset='UTF-8'>"
        html += "<style>"
        html += "body { font-family: Arial, sans-serif; margin: 0; padding: 0; width: 100%; }"
        html += "table { width: 100%; border-collapse: collapse; table-layout: fixed; }"
        html += "th { background-color: #f2f2f2; padding: 12px 5px; border: 2px solid #000; font-weight: bold; font-size: 14pt; text-align: center; }"
        html += "td { border: 2px solid #000; padding: 8px 5px; vertical-align: top; font-size: 12pt; width: 14%; }"
        html += ".repas { margin-bottom: 15px; page-break-inside: avoid; }"
        html += (
            ".repas-title { font-weight: bold; margin-bottom: 8px; font-size: 10pt; }"
        )
        html += ".aliment { margin-left: 10px; margin-bottom: 6px; font-size: 8pt; }"
        html += "* { -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }"
        html += "@page { size: landscape; margin: 1cm; }"
        html += "</style>"
        html += "</head><body>"

        # Créer directement le tableau
        html += "<table>"

        # En-tête du tableau
        html += "<tr>"
        for jour in jours:
            html += f"<th>{jour}</th>"
        html += "</tr>"

        # Contenu du tableau
        html += "<tr>"
        for jour in jours:
            html += "<td>"

            for repas in repas_semaine[jour]:
                html += f"<div class='repas'>"
                html += f"<div class='repas-title'>{repas['nom']}</div>"

                if repas["aliments"]:
                    for aliment in repas["aliments"]:
                        html += f"<div class='aliment'>• {aliment['nom']} ({aliment['quantite']}g)</div>"
                else:
                    html += "<div class='aliment'>Aucun aliment</div>"

                html += "</div>"

            html += "</td>"

        html += "</tr>"
        html += "</table>"
        html += "</body></html>"

        return html

    def on_aliment_supprime(self, aliment_id):
        """Appelé lorsqu'un aliment est supprimé"""
        # Rafraîchir les données de cette semaine
        self.load_data()
