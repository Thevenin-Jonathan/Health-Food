from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QFrame,
    QFormLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QFont


class CustomProgressBar(QProgressBar):
    """Barre de progression personnalisée avec une marque à 100%"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_value = 100  # Valeur cible (100%)

    # pylint: disable=invalid-name
    def paintEvent(self, event):
        # Laisser la classe parente dessiner la barre de base
        super().paintEvent(event)

        # Dessiner une ligne verticale à la position 100%
        if self.maximum() > 0:
            painter = QPainter(self)

            # Définir un stylo plus visible
            pen = QPen(QColor(0, 0, 0))  # Noir
            pen.setWidth(2)
            painter.setPen(pen)

            # Calculer la position x pour 100% (la valeur cible)
            x_pos = int((100.0 / self.maximum()) * self.width())

            # Dessiner la ligne verticale sur toute la hauteur
            painter.drawLine(x_pos, 0, x_pos, self.height())

            painter.end()


class NutritionComparison(QWidget):
    """Widget pour comparer les valeurs nutritionnelles entre deux repas"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        # Valeurs par défaut au cas où aucun objectif utilisateur n'est disponible
        self.user_cal_target = 2500
        self.user_prot_target = 180
        self.user_gluc_target = 250
        self.user_lip_target = 70
        # Charger les objectifs de l'utilisateur
        self.load_user_targets()
        self.setup_ui()

    def load_user_targets(self):
        """Charge les objectifs nutritionnels depuis le profil utilisateur"""
        if not self.db_manager:
            return

        user_data = self.db_manager.get_utilisateur()
        if user_data:
            # Récupérer les objectifs caloriques et macros
            self.user_cal_target = user_data.get("objectif_calories", 2500) or 2500
            self.user_prot_target = user_data.get("objectif_proteines", 180) or 180
            self.user_gluc_target = user_data.get("objectif_glucides", 250) or 250
            self.user_lip_target = user_data.get("objectif_lipides", 70) or 70

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Titre
        title = QLabel("<h3>Comparaison nutritionnelle</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Tableau de comparaison
        self.comparison_table = QTableWidget()
        self.comparison_table.setObjectName("comparisonTable")  # Pour le ciblage CSS
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setHorizontalHeaderLabels(
            ["Nutriment", "Repas actuel", "Nouveau repas", "Différence"]
        )

        # Corriger la hauteur des en-têtes et lignes
        self.comparison_table.horizontalHeader().setMinimumHeight(30)
        self.comparison_table.verticalHeader().setDefaultSectionSize(30)

        # Configurer les colonnes
        self.comparison_table.setColumnWidth(0, 150)  # Nutriment
        self.comparison_table.setColumnWidth(1, 120)  # Repas actuel
        self.comparison_table.setColumnWidth(2, 120)  # Nouveau repas
        self.comparison_table.setColumnWidth(3, 120)  # Différence

        # Configurer les modes de redimensionnement
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )

        # Largeur minimale pour la première colonne
        self.comparison_table.setColumnWidth(0, 90)

        # Désactiver le scrolling horizontal
        self.comparison_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Optimiser l'apparence
        self.comparison_table.setAlternatingRowColors(True)
        self.comparison_table.verticalHeader().setVisible(
            False
        )  # Masquer les en-têtes de ligne verticaux
        self.comparison_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comparison_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Ajouter des lignes pour les macros
        self.comparison_table.setRowCount(6)  # 5 macros + coût
        self.comparison_table.setItem(0, 0, QTableWidgetItem("Calories"))
        self.comparison_table.setItem(1, 0, QTableWidgetItem("Protéines"))
        self.comparison_table.setItem(2, 0, QTableWidgetItem("Glucides"))
        self.comparison_table.setItem(3, 0, QTableWidgetItem("Lipides"))
        self.comparison_table.setItem(4, 0, QTableWidgetItem("Fibres"))
        self.comparison_table.setItem(5, 0, QTableWidgetItem("Coût estimé"))

        # Ajouter le tableau au layout
        layout.addWidget(self.comparison_table)

        # Séparateur horizontal pour meilleure lisibilité visuelle
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { margin: 10px 0; }")
        layout.addWidget(separator)

        # Zone de prévision journalière avec titre unique et explicite
        nutritional_impact_label = QLabel(
            "<b>Impact nutritionnel journalier si le repas est remplacé</b>"
        )
        nutritional_impact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(nutritional_impact_label)

        # Conteneur extérieur pour tout le bloc des barres de progression
        outer_container = QWidget()
        outer_layout = QVBoxLayout(outer_container)
        outer_layout.setContentsMargins(0, 10, 0, 0)

        # Ligne avec le marqueur 100%
        marker_widget = QWidget()
        marker_layout = QHBoxLayout(marker_widget)
        marker_layout.setContentsMargins(0, 0, 0, 0)

        # Ajouter un widget de taille fixe pour espacer le marqueur correctement
        # Cet espacement doit tenir compte de la largeur des libellés + l'espacement
        label_width = 70  # Largeur approximative des libellés (Calories:, etc.)
        layout_spacing = 10  # Espacement du layout

        # La position 100% se trouve à 71.4% (100/140) de la largeur de la barre de 300px
        # Ajustement pour que le texte "100%" soit centré exactement sur la ligne verticale
        marker_position = (
            label_width + layout_spacing + (300 * 0.714) - 35
        )  # Ajusté de -10 à -15

        # Label vide avec la largeur appropriée
        spacer_label = QLabel("")
        spacer_label.setFixedWidth(marker_position)
        marker_layout.addWidget(spacer_label)

        # Le label 100%
        hundred_label = QLabel("100%")
        hundred_label.setFont(QFont("Arial", 9, QFont.Bold))
        hundred_label.setAlignment(Qt.AlignCenter)  # Centrage du texte
        hundred_label.setFixedWidth(
            30
        )  # Largeur fixe pour un meilleur contrôle du centrage
        marker_layout.addWidget(hundred_label)

        # Ajouter du stretch pour pousser le label à gauche
        marker_layout.addStretch(1)

        # Ajouter le widget du marqueur au layout extérieur
        outer_layout.addWidget(marker_widget)

        # Layout pour les barres de progression avec leurs labels
        progress_layout = QFormLayout()
        progress_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        # Style commun pour toutes les barres de progression
        progress_bar_style = """
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                margin: 0px;
                padding: 0px;
                min-width: 300px;
                max-width: 300px;
            }
        """

        # Créer les barres de progression et les ajouter au layout
        self.cal_impact = self._create_custom_progress_bar(progress_bar_style)
        self.prot_impact = self._create_custom_progress_bar(progress_bar_style)
        self.gluc_impact = self._create_custom_progress_bar(progress_bar_style)
        self.lip_impact = self._create_custom_progress_bar(progress_bar_style)

        progress_layout.addRow("Calories:", self.cal_impact)
        progress_layout.addRow("Protéines:", self.prot_impact)
        progress_layout.addRow("Glucides:", self.gluc_impact)
        progress_layout.addRow("Lipides:", self.lip_impact)

        # Ajouter le layout des barres au conteneur extérieur
        outer_layout.addLayout(progress_layout)

        # Ajouter tout le bloc au layout principal
        layout.addWidget(outer_container)

    def _create_custom_progress_bar(self, style):
        """Crée une barre de progression personnalisée"""
        progress_bar = CustomProgressBar()
        progress_bar.setMaximum(140)  # Maximum fixe à 140%
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("%v / %m")
        progress_bar.setStyleSheet(style)
        return progress_bar

    def update_comparison(self, repas_actuel, repas_nouveau, totaux_jour=None):
        """Met à jour la comparaison avec les données des deux repas"""
        # Calories
        cal_actuel = QTableWidgetItem(f"{repas_actuel['total_calories']:.0f} kcal")
        cal_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(0, 1, cal_actuel)

        cal_nouveau = QTableWidgetItem(f"{repas_nouveau['total_calories']:.0f} kcal")
        cal_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(0, 2, cal_nouveau)

        diff_cal = repas_nouveau["total_calories"] - repas_actuel["total_calories"]
        diff_cal_item = QTableWidgetItem(f"{diff_cal:+.0f} kcal")
        diff_cal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if diff_cal > 0:
            diff_cal_item.setForeground(QBrush(QColor("red")))
        elif diff_cal < 0:
            diff_cal_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(0, 3, diff_cal_item)

        # Protéines
        prot_actuel = QTableWidgetItem(f"{repas_actuel['total_proteines']:.1f} g")
        prot_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(1, 1, prot_actuel)

        prot_nouveau = QTableWidgetItem(f"{repas_nouveau['total_proteines']:.1f} g")
        prot_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(1, 2, prot_nouveau)

        diff_prot = repas_nouveau["total_proteines"] - repas_actuel["total_proteines"]
        diff_prot_item = QTableWidgetItem(f"{diff_prot:+.1f} g")
        diff_prot_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if diff_prot > 0:
            diff_prot_item.setForeground(QBrush(QColor("green")))
        elif diff_prot < 0:
            diff_prot_item.setForeground(QBrush(QColor("red")))
        self.comparison_table.setItem(1, 3, diff_prot_item)

        # Glucides
        gluc_actuel = QTableWidgetItem(f"{repas_actuel['total_glucides']:.1f} g")
        gluc_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(2, 1, gluc_actuel)

        gluc_nouveau = QTableWidgetItem(f"{repas_nouveau['total_glucides']:.1f} g")
        gluc_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(2, 2, gluc_nouveau)

        diff_gluc = repas_nouveau["total_glucides"] - repas_actuel["total_glucides"]
        diff_gluc_item = QTableWidgetItem(f"{diff_gluc:+.1f} g")
        diff_gluc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if abs(diff_gluc) < 5:  # Petite différence -> neutre
            pass
        elif diff_gluc > 0:
            diff_gluc_item.setForeground(QBrush(QColor("orange")))
        else:
            diff_gluc_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(2, 3, diff_gluc_item)

        # Lipides
        lip_actuel = QTableWidgetItem(f"{repas_actuel['total_lipides']:.1f} g")
        lip_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(3, 1, lip_actuel)

        lip_nouveau = QTableWidgetItem(f"{repas_nouveau['total_lipides']:.1f} g")
        lip_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(3, 2, lip_nouveau)

        diff_lip = repas_nouveau["total_lipides"] - repas_actuel["total_lipides"]
        diff_lip_item = QTableWidgetItem(f"{diff_lip:+.1f} g")
        diff_lip_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if abs(diff_lip) < 2:  # Petite différence -> neutre
            pass
        elif diff_lip > 0:
            diff_lip_item.setForeground(QBrush(QColor("orange")))
        else:
            diff_lip_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(3, 3, diff_lip_item)

        # Fibres
        total_fibres_actuel = sum(
            (a.get("fibres", 0) * a["quantite"] / 100) for a in repas_actuel["aliments"]
        )
        total_fibres_nouveau = sum(
            (a.get("fibres", 0) * a["quantite"] / 100)
            for a in repas_nouveau["aliments"]
        )

        fibres_actuel = QTableWidgetItem(f"{total_fibres_actuel:.1f} g")
        fibres_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(4, 1, fibres_actuel)

        fibres_nouveau = QTableWidgetItem(f"{total_fibres_nouveau:.1f} g")
        fibres_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(4, 2, fibres_nouveau)

        diff_fibre = total_fibres_nouveau - total_fibres_actuel
        diff_fibre_item = QTableWidgetItem(f"{diff_fibre:+.1f} g")
        diff_fibre_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if diff_fibre > 0:
            diff_fibre_item.setForeground(QBrush(QColor("green")))
        elif diff_fibre < 0:
            diff_fibre_item.setForeground(QBrush(QColor("red")))
        self.comparison_table.setItem(4, 3, diff_fibre_item)

        # Coût estimé
        total_cout_actuel = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_actuel["aliments"]
        )
        total_cout_nouveau = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_nouveau["aliments"]
        )

        cout_actuel = QTableWidgetItem(f"{total_cout_actuel:.2f} €")
        cout_actuel.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(5, 1, cout_actuel)

        cout_nouveau = QTableWidgetItem(f"{total_cout_nouveau:.2f} €")
        cout_nouveau.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comparison_table.setItem(5, 2, cout_nouveau)

        diff_cout = total_cout_nouveau - total_cout_actuel
        diff_cout_item = QTableWidgetItem(f"{diff_cout:+.2f} €")
        diff_cout_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if diff_cout > 0:
            diff_cout_item.setForeground(QBrush(QColor("red")))
        elif diff_cout < 0:
            diff_cout_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(5, 3, diff_cout_item)

        # Mise à jour de l'impact sur la journée si les données sont disponibles
        if totaux_jour:
            # Calculer les nouveaux totaux en supprimant UNIQUEMENT l'ancien repas
            # et en ajoutant le nouveau (le reste des repas reste inchangé)
            # Cela donne une prévision correcte de l'impact sur la journée

            # Les totaux_jour actuels incluent déjà le repas actuel
            # Donc on soustrait le repas actuel et on ajoute le nouveau
            new_cal = (
                totaux_jour["calories"]
                - repas_actuel["total_calories"]
                + repas_nouveau["total_calories"]
            )
            new_prot = (
                totaux_jour["proteines"]
                - repas_actuel["total_proteines"]
                + repas_nouveau["total_proteines"]
            )
            new_gluc = (
                totaux_jour["glucides"]
                - repas_actuel["total_glucides"]
                + repas_nouveau["total_glucides"]
            )
            new_lip = (
                totaux_jour["lipides"]
                - repas_actuel["total_lipides"]
                + repas_nouveau["total_lipides"]
            )

            # Utiliser les objectifs nutritionnels de l'utilisateur
            cal_target = self.user_cal_target
            prot_target = self.user_prot_target
            gluc_target = self.user_gluc_target
            lip_target = self.user_lip_target

            # Mise à jour des barres avec un maximum fixe
            def update_progress_bar(progress_bar, value, target):
                # Stocker les valeurs pour l'affichage et le tooltip
                progress_bar.target_value = int(target)

                # Calculer la valeur en pourcentage de l'objectif (100% = objectif atteint)
                percentage_value = int((value / target) * 100)

                # Limiter à la valeur maximum (140%)
                display_value = min(percentage_value, 140)

                # Définir la valeur
                progress_bar.setValue(display_value)

                # Format texte personnalisé pour afficher la valeur réelle par rapport à l'objectif
                progress_bar.setFormat(f"{value:.0f} / {target:.0f}")

            # Appliquer les mises à jour
            update_progress_bar(self.cal_impact, new_cal, cal_target)
            update_progress_bar(self.prot_impact, new_prot, prot_target)
            update_progress_bar(self.gluc_impact, new_gluc, gluc_target)
            update_progress_bar(self.lip_impact, new_lip, lip_target)

            # Colorer les barres selon l'écart par rapport aux objectifs
            self._set_progress_bar_color(self.cal_impact, new_cal / cal_target)
            self._set_progress_bar_color(self.prot_impact, new_prot / prot_target)
            self._set_progress_bar_color(self.gluc_impact, new_gluc / gluc_target)
            self._set_progress_bar_color(self.lip_impact, new_lip / lip_target)

            # Force le réajustement du marker 100%
            QTimer.singleShot(50, self.update)

    def _set_progress_bar_color(self, progress_bar, ratio):
        """Configure la couleur de la barre de progression selon des seuils précis"""
        # Couleur de base pour la barre de progression
        base_style = """
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                margin: 0px;
                padding: 0px;
                min-width: 300px;
                max-width: 300px;
            }
        """

        # Déterminer la couleur selon les seuils
        if 0.9 <= ratio <= 1.1:
            # Zone optimale: vert
            color_style = "QProgressBar::chunk { background-color: #2ecc71; }"  # Vert
            tooltip_text = "Optimal (90-110%)"
        elif ratio < 0.2:
            # Très bas: rouge
            color_style = "QProgressBar::chunk { background-color: #e74c3c; }"  # Rouge
            tooltip_text = f"Très insuffisant ({ratio*100:.0f}%)"
        elif ratio < 0.55:
            # Bas: orange
            color_style = "QProgressBar::chunk { background-color: #e67e22; }"  # Orange
            tooltip_text = f"Insuffisant ({ratio*100:.0f}%)"
        elif ratio < 0.9:
            # Moyen: jaune
            color_style = "QProgressBar::chunk { background-color: #f1c40f; }"  # Jaune
            tooltip_text = f"Légèrement insuffisant ({ratio*100:.0f}%)"
        elif ratio <= 1.2:
            # Légèrement élevé: jaune
            color_style = "QProgressBar::chunk { background-color: #f1c40f; }"  # Jaune
            tooltip_text = f"Légèrement excessif ({ratio*100:.0f}%)"
        elif ratio <= 1.3:
            # Élevé: orange
            color_style = "QProgressBar::chunk { background-color: #e67e22; }"  # Orange
            tooltip_text = f"Excessif ({ratio*100:.0f}%)"
        else:
            # Très élevé: rouge
            color_style = "QProgressBar::chunk { background-color: #e74c3c; }"  # Rouge
            tooltip_text = f"Très excessif ({ratio*100:.0f}%)"

        # Appliquer le style
        progress_bar.setStyleSheet(base_style + color_style)

        # Définir le tooltip
        progress_bar.setToolTip(tooltip_text)
