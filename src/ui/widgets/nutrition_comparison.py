from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QProgressBar,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QFont


class CustomProgressBar(QProgressBar):
    """Barre de progression personnalisée avec une marque à 100%"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_value = 100  # Valeur cible (100%)

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

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
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setHorizontalHeaderLabels(
            ["Nutriment", "Repas actuel", "Nouveau repas", "Différence"]
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.comparison_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )

        # Ajouter des lignes pour les macros - incluant les fibres et coût
        self.comparison_table.setRowCount(6)  # 5 macros + coût
        self.comparison_table.setItem(0, 0, QTableWidgetItem("Calories"))
        self.comparison_table.setItem(1, 0, QTableWidgetItem("Protéines"))
        self.comparison_table.setItem(2, 0, QTableWidgetItem("Glucides"))
        self.comparison_table.setItem(3, 0, QTableWidgetItem("Lipides"))
        self.comparison_table.setItem(4, 0, QTableWidgetItem("Fibres"))
        self.comparison_table.setItem(5, 0, QTableWidgetItem("Coût estimé"))

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
        self.fibre_impact = self._create_custom_progress_bar(progress_bar_style)

        progress_layout.addRow("Calories:", self.cal_impact)
        progress_layout.addRow("Protéines:", self.prot_impact)
        progress_layout.addRow("Glucides:", self.gluc_impact)
        progress_layout.addRow("Lipides:", self.lip_impact)
        progress_layout.addRow("Fibres:", self.fibre_impact)

        # Ajouter le layout des barres au conteneur extérieur
        outer_layout.addLayout(progress_layout)

        # Ajouter tout le bloc au layout principal
        layout.addWidget(outer_container)

    def _create_custom_progress_bar(self, style):
        """Crée une barre de progression personnalisée"""
        bar = CustomProgressBar()
        bar.setMaximum(140)  # Maximum fixe à 140%
        bar.setTextVisible(True)
        bar.setFormat("%v / %m")
        bar.setStyleSheet(style)
        return bar

    def update_comparison(self, repas_actuel, repas_nouveau, totaux_jour=None):
        """Met à jour la comparaison avec les données des deux repas"""
        # Calories
        self.comparison_table.setItem(
            0, 1, QTableWidgetItem(f"{repas_actuel['total_calories']:.0f} kcal")
        )
        self.comparison_table.setItem(
            0, 2, QTableWidgetItem(f"{repas_nouveau['total_calories']:.0f} kcal")
        )

        diff_cal = repas_nouveau["total_calories"] - repas_actuel["total_calories"]
        diff_cal_item = QTableWidgetItem(f"{diff_cal:+.0f} kcal")
        if diff_cal > 0:
            diff_cal_item.setForeground(QBrush(QColor("red")))
        elif diff_cal < 0:
            diff_cal_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(0, 3, diff_cal_item)

        # Protéines
        self.comparison_table.setItem(
            1, 1, QTableWidgetItem(f"{repas_actuel['total_proteines']:.1f} g")
        )
        self.comparison_table.setItem(
            1, 2, QTableWidgetItem(f"{repas_nouveau['total_proteines']:.1f} g")
        )

        diff_prot = repas_nouveau["total_proteines"] - repas_actuel["total_proteines"]
        diff_prot_item = QTableWidgetItem(f"{diff_prot:+.1f} g")
        if diff_prot > 0:
            diff_prot_item.setForeground(QBrush(QColor("green")))
        elif diff_prot < 0:
            diff_prot_item.setForeground(QBrush(QColor("red")))
        self.comparison_table.setItem(1, 3, diff_prot_item)

        # Glucides
        self.comparison_table.setItem(
            2, 1, QTableWidgetItem(f"{repas_actuel['total_glucides']:.1f} g")
        )
        self.comparison_table.setItem(
            2, 2, QTableWidgetItem(f"{repas_nouveau['total_glucides']:.1f} g")
        )

        diff_gluc = repas_nouveau["total_glucides"] - repas_actuel["total_glucides"]
        diff_gluc_item = QTableWidgetItem(f"{diff_gluc:+.1f} g")
        if abs(diff_gluc) < 5:  # Petite différence -> neutre
            pass
        elif diff_gluc > 0:
            diff_gluc_item.setForeground(QBrush(QColor("orange")))
        else:
            diff_gluc_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(2, 3, diff_gluc_item)

        # Lipides
        self.comparison_table.setItem(
            3, 1, QTableWidgetItem(f"{repas_actuel['total_lipides']:.1f} g")
        )
        self.comparison_table.setItem(
            3, 2, QTableWidgetItem(f"{repas_nouveau['total_lipides']:.1f} g")
        )

        diff_lip = repas_nouveau["total_lipides"] - repas_actuel["total_lipides"]
        diff_lip_item = QTableWidgetItem(f"{diff_lip:+.1f} g")
        if abs(diff_lip) < 2:  # Petite différence -> neutre
            pass
        elif diff_lip > 0:
            diff_lip_item.setForeground(QBrush(QColor("orange")))
        else:
            diff_lip_item.setForeground(QBrush(QColor("green")))
        self.comparison_table.setItem(3, 3, diff_lip_item)

        # Fibres - Nouveau
        total_fibres_actuel = sum(
            (a.get("fibres", 0) * a["quantite"] / 100) for a in repas_actuel["aliments"]
        )
        total_fibres_nouveau = sum(
            (a.get("fibres", 0) * a["quantite"] / 100)
            for a in repas_nouveau["aliments"]
        )

        self.comparison_table.setItem(
            4, 1, QTableWidgetItem(f"{total_fibres_actuel:.1f} g")
        )
        self.comparison_table.setItem(
            4, 2, QTableWidgetItem(f"{total_fibres_nouveau:.1f} g")
        )

        diff_fibre = total_fibres_nouveau - total_fibres_actuel
        diff_fibre_item = QTableWidgetItem(f"{diff_fibre:+.1f} g")
        if diff_fibre > 0:
            diff_fibre_item.setForeground(QBrush(QColor("green")))
        elif diff_fibre < 0:
            diff_fibre_item.setForeground(QBrush(QColor("red")))
        self.comparison_table.setItem(4, 3, diff_fibre_item)

        # Coût estimé - Nouveau
        total_cout_actuel = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_actuel["aliments"]
        )
        total_cout_nouveau = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_nouveau["aliments"]
        )

        self.comparison_table.setItem(
            5, 1, QTableWidgetItem(f"{total_cout_actuel:.2f} €")
        )
        self.comparison_table.setItem(
            5, 2, QTableWidgetItem(f"{total_cout_nouveau:.2f} €")
        )

        diff_cout = total_cout_nouveau - total_cout_actuel
        diff_cout_item = QTableWidgetItem(f"{diff_cout:+.2f} €")
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

            # Fibres totales
            # D'abord calculer les fibres actuelles du repas
            total_fibres_actuel = sum(
                (a.get("fibres", 0) * a["quantite"] / 100)
                for a in repas_actuel["aliments"]
            )
            total_fibres_nouveau = sum(
                (a.get("fibres", 0) * a["quantite"] / 100)
                for a in repas_nouveau["aliments"]
            )

            # Si les fibres sont disponibles dans les totaux, les utiliser, sinon les estimer
            if "fibres" in totaux_jour:
                new_fibre = (
                    totaux_jour["fibres"] - total_fibres_actuel + total_fibres_nouveau
                )
            else:
                # Si pas de totaux disponibles, utiliser juste la valeur du nouveau repas
                new_fibre = total_fibres_nouveau

            # Objectifs nutritionnels (à personnaliser ou à récupérer des préférences utilisateur)
            cal_target = 2500
            prot_target = 180
            gluc_target = 250
            lip_target = 70
            fibre_target = 30

            # Mise à jour des barres avec un maximum fixe
            def update_progress_bar(bar, value, target):
                # Stocker les valeurs pour l'affichage et le tooltip
                bar.target_value = int(target)

                # Calculer la valeur en pourcentage de l'objectif (100% = objectif atteint)
                percentage_value = int((value / target) * 100)

                # Limiter à la valeur maximum (140%)
                display_value = min(percentage_value, 140)

                # Définir la valeur
                bar.setValue(display_value)

                # Format texte personnalisé pour afficher la valeur réelle par rapport à l'objectif
                bar.setFormat(f"{value:.0f} / {target:.0f}")

            # Appliquer les mises à jour
            update_progress_bar(self.cal_impact, new_cal, cal_target)
            update_progress_bar(self.prot_impact, new_prot, prot_target)
            update_progress_bar(self.gluc_impact, new_gluc, gluc_target)
            update_progress_bar(self.lip_impact, new_lip, lip_target)
            update_progress_bar(self.fibre_impact, new_fibre, fibre_target)

            # Colorer les barres selon l'écart par rapport aux objectifs
            self._set_progress_bar_color(self.cal_impact, new_cal / cal_target)
            self._set_progress_bar_color(self.prot_impact, new_prot / prot_target)
            self._set_progress_bar_color(self.gluc_impact, new_gluc / gluc_target)
            self._set_progress_bar_color(self.lip_impact, new_lip / lip_target)
            self._set_progress_bar_color(self.fibre_impact, new_fibre / fibre_target)

            # Force le réajustement du marker 100%
            QTimer.singleShot(50, self.update)

    def _set_progress_bar_color(self, bar, ratio):
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
        bar.setStyleSheet(base_style + color_style)

        # Définir le tooltip
        bar.setToolTip(tooltip_text)
