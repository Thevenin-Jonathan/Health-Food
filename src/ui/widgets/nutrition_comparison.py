from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QFrame,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPen


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
        title.setProperty("class", "group-title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # NOUVELLE IMPLÉMENTATION: Remplacer le QTableWidget par un cadre stylisé
        comparison_frame = QFrame()
        comparison_frame.setObjectName("comparison-frame")
        comparison_frame.setProperty("class", "nutrition-summary")
        comparison_frame.setFrameShape(QFrame.StyledPanel)
        comparison_frame.setMaximumWidth(600)  # Plus large pour les 4 colonnes

        comparison_layout = QGridLayout(comparison_frame)
        comparison_layout.setContentsMargins(15, 15, 15, 15)
        comparison_layout.setVerticalSpacing(10)
        comparison_layout.setHorizontalSpacing(15)

        # En-têtes pour les 4 colonnes
        headers = ["Nutriment", "Repas actuel", "Nouveau repas", "Différence"]
        for col, text in enumerate(headers):
            header = QLabel(text)
            header.setProperty("class", "nutrition-subtitle")
            header.setAlignment(Qt.AlignCenter)
            comparison_layout.addWidget(header, 0, col)

        # Ligne de séparation sous les en-têtes
        separator_container = QWidget()
        separator_container_layout = QHBoxLayout(separator_container)
        separator_container_layout.setContentsMargins(5, 0, 5, 0)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #d1e3fa; margin: 5px 0px;")
        separator.setMaximumHeight(2)

        separator_container_layout.addWidget(separator)
        comparison_layout.addWidget(separator_container, 1, 0, 1, 4)

        # Structure des données nutritionnelles pour la comparaison
        comparison_data = [
            ("🔥", "Calories", "calories", "kcal"),
            ("🥩", "Protéines", "proteines", "g"),
            ("🍞", "Glucides", "glucides", "g"),
            ("🥑", "Lipides", "lipides", "g"),
            ("🌱", "Fibres", "fibres", "g"),
            ("💰", "Coût", "cout", "€"),
        ]

        # Créer les labels pour chaque ligne de la comparaison
        for row, (icon, label_text, attr_name, unit) in enumerate(comparison_data, 2):
            # Colonne 0: Icône + nom du nutriment
            nutriment_container = QWidget()
            nutriment_layout = QHBoxLayout(nutriment_container)
            nutriment_layout.setContentsMargins(0, 0, 0, 0)
            nutriment_layout.setSpacing(5)

            # Icône
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedWidth(25)
            nutriment_layout.addWidget(icon_label)

            # Nom du nutriment
            name_label = QLabel(label_text)
            name_label.setProperty("class", "nutrition-subtitle")
            nutriment_layout.addWidget(name_label)

            comparison_layout.addWidget(nutriment_container, row, 0)

            # Colonne 1: Repas actuel
            current_val = QLabel("0" + f" {unit}")
            current_val.setProperty("class", "comparison-value")
            current_val.setAlignment(Qt.AlignCenter)
            setattr(self, f"compare_current_{attr_name}", current_val)
            comparison_layout.addWidget(current_val, row, 1)

            # Colonne 2: Nouveau repas
            new_val = QLabel("0" + f" {unit}")
            new_val.setProperty("class", "comparison-value")
            new_val.setAlignment(Qt.AlignCenter)
            setattr(self, f"compare_new_{attr_name}", new_val)
            comparison_layout.addWidget(new_val, row, 2)

            # Colonne 3: Différence (avec affichage +/-)
            diff_val = QLabel("0" + f" {unit}")
            diff_val.setProperty("class", "comparison-diff")
            diff_val.setAlignment(Qt.AlignCenter)
            setattr(self, f"compare_diff_{attr_name}", diff_val)
            comparison_layout.addWidget(diff_val, row, 3)

        # Centrer le cadre de comparaison
        comparison_container = QHBoxLayout()
        comparison_container.addStretch()
        comparison_container.addWidget(comparison_frame)
        comparison_container.addStretch()

        layout.addLayout(comparison_container)

        # Conserver le tableau existant pour des raisons de compatibilité
        # mais le masquer (on utilisera les nouveaux labels)
        self.comparison_table = QTableWidget()
        self.comparison_table.setObjectName("comparisonTable")
        self.comparison_table.setColumnCount(4)
        self.comparison_table.setRowCount(6)
        self.comparison_table.setHidden(True)

        # Séparateur horizontal
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { margin: 10px 0; }")
        layout.addWidget(separator)

        # Titre de l'impact nutritionnel journalier
        nutritional_impact_label = QLabel("<h3>Impact nutritionnel journalier</h3>")
        nutritional_impact_label.setProperty("class", "group-title")
        nutritional_impact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(nutritional_impact_label)

        # Cadre amélioré avec 3 colonnes: actuel, objectif, nouveau
        nutrition_frame = QFrame()
        nutrition_frame.setObjectName("nutrition-frame")
        nutrition_frame.setProperty("class", "nutrition-summary")
        nutrition_frame.setFrameShape(QFrame.StyledPanel)
        nutrition_frame.setMaximumWidth(500)  # Plus large pour accommoder 3 colonnes

        nutrition_layout = QGridLayout(nutrition_frame)
        nutrition_layout.setContentsMargins(15, 15, 15, 15)
        nutrition_layout.setVerticalSpacing(10)
        nutrition_layout.setHorizontalSpacing(10)

        # En-têtes pour les 3 colonnes
        headers = ["Nutriment", "Actuel", "Objectif", "Nouveau"]
        for col, text in enumerate(headers):
            header = QLabel(text)
            header.setProperty("class", "nutrition-subtitle")
            header.setAlignment(Qt.AlignCenter)
            nutrition_layout.addWidget(header, 0, col)

        # Ligne de séparation sous les en-têtes
        separator_container = QWidget()
        separator_container_layout = QHBoxLayout(separator_container)
        separator_container_layout.setContentsMargins(5, 0, 5, 0)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #d1e3fa; margin: 5px 0px;")
        separator2.setMaximumHeight(2)

        separator_container_layout.addWidget(separator2)
        nutrition_layout.addWidget(separator_container, 1, 0, 1, 4)

        # Structure des données nutritionnelles avec icônes
        nutrition_data = [
            ("🔥", "Calories", "calories", "kcal", "user_cal_target"),
            ("🥩", "Protéines", "proteines", "g", "user_prot_target"),
            ("🍞", "Glucides", "glucides", "g", "user_gluc_target"),
            ("🥑", "Lipides", "lipides", "g", "user_lip_target"),
        ]

        # Créer les lignes pour chaque nutriment
        for row, (icon, label_text, attr_name, unit, target_attr) in enumerate(
            nutrition_data, 2
        ):
            # Colonne 0: Icône + nom du nutriment
            nutriment_container = QWidget()
            nutriment_layout = QHBoxLayout(nutriment_container)
            nutriment_layout.setContentsMargins(0, 0, 0, 0)
            nutriment_layout.setSpacing(5)

            # Icône
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedWidth(25)
            nutriment_layout.addWidget(icon_label)

            # Nom du nutriment
            name_label = QLabel(label_text)
            name_label.setProperty("class", "nutrition-subtitle")
            nutriment_layout.addWidget(name_label)

            nutrition_layout.addWidget(nutriment_container, row, 0)

            # Colonne 1: Valeur actuelle
            current_val = QLabel("0" + f" {unit}")
            current_val.setProperty("class", "nutrition-value")
            current_val.setProperty("type", attr_name)
            current_val.setAlignment(Qt.AlignCenter)
            setattr(self, f"current_{attr_name}", current_val)
            nutrition_layout.addWidget(current_val, row, 1)

            # Colonne 2: Objectif journalier
            target_val = QLabel(f"{getattr(self, target_attr)}" + f" {unit}")
            target_val.setProperty("class", "target-value")
            target_val.setAlignment(Qt.AlignCenter)
            target_val.setStyleSheet("color: #777; font-weight: bold;")
            setattr(self, f"target_{attr_name}", target_val)
            nutrition_layout.addWidget(target_val, row, 2)

            # Colonne 3: Nouvelle valeur après modification
            new_val = QLabel("0" + f" {unit}")
            new_val.setProperty("class", "result-value-highlight")
            new_val.setProperty("type", attr_name)
            new_val.setAlignment(Qt.AlignCenter)
            setattr(self, f"new_{attr_name}", new_val)
            nutrition_layout.addWidget(new_val, row, 3)

        # Ligne pour les pourcentages
        percent_row = nutrition_layout.rowCount()
        percent_label = QLabel("% des objectifs:")
        percent_label.setProperty("class", "hint")
        percent_label.setAlignment(Qt.AlignLeft)
        nutrition_layout.addWidget(percent_label, percent_row, 0)

        # Pourcentage actuel
        self.percent_current = QLabel("0%")
        self.percent_current.setAlignment(Qt.AlignCenter)
        self.percent_current.setProperty("class", "hint")
        nutrition_layout.addWidget(self.percent_current, percent_row, 1)

        # Case vide pour la colonne objectif (pour alignement)
        empty_label = QLabel("")
        nutrition_layout.addWidget(empty_label, percent_row, 2)

        # Pourcentage nouveau
        self.percent_new = QLabel("0%")
        self.percent_new.setAlignment(Qt.AlignCenter)
        self.percent_new.setProperty("class", "hint")
        nutrition_layout.addWidget(self.percent_new, percent_row, 3)

        # Centrer le cadre nutritionnel
        nutrition_container = QHBoxLayout()
        nutrition_container.addStretch()
        nutrition_container.addWidget(nutrition_frame)
        nutrition_container.addStretch()

        layout.addLayout(nutrition_container)

    def _get_status_color(self, status):
        """Retourne la couleur CSS correspondant au statut"""
        colors = {
            "over": "#c62828",  # Rouge - trop élevé
            "good": "#2e7d32",  # Vert - optimal
            "medium": "#f57f17",  # Orange - moyen
            "low": "#757575",  # Gris - insuffisant
            "neutral": "",  # Pas de couleur spécifique
        }
        return colors.get(status, "")

    def update_comparison(self, repas_actuel, repas_nouveau, totaux_jour=None):
        """Met à jour la comparaison avec les données des deux repas"""

        # Calories
        self.compare_current_calories.setText(
            f"{repas_actuel['total_calories']:.0f} kcal"
        )
        self.compare_new_calories.setText(f"{repas_nouveau['total_calories']:.0f} kcal")

        diff_cal = repas_nouveau["total_calories"] - repas_actuel["total_calories"]
        self.compare_diff_calories.setText(f"{diff_cal:+.0f} kcal")
        if diff_cal > 0:
            self.compare_diff_calories.setStyleSheet(
                f"color: {self._get_status_color('over')}; font-weight: bold;"
            )
        elif diff_cal < 0:
            self.compare_diff_calories.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )
        else:
            self.compare_diff_calories.setStyleSheet("")

        # Protéines
        self.compare_current_proteines.setText(
            f"{repas_actuel['total_proteines']:.1f} g"
        )
        self.compare_new_proteines.setText(f"{repas_nouveau['total_proteines']:.1f} g")

        diff_prot = repas_nouveau["total_proteines"] - repas_actuel["total_proteines"]
        self.compare_diff_proteines.setText(f"{diff_prot:+.1f} g")
        if diff_prot > 0:
            self.compare_diff_proteines.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )
        elif diff_prot < 0:
            self.compare_diff_proteines.setStyleSheet(
                f"color: {self._get_status_color('over')}; font-weight: bold;"
            )
        else:
            self.compare_diff_proteines.setStyleSheet("")

        # Glucides
        self.compare_current_glucides.setText(f"{repas_actuel['total_glucides']:.1f} g")
        self.compare_new_glucides.setText(f"{repas_nouveau['total_glucides']:.1f} g")

        diff_gluc = repas_nouveau["total_glucides"] - repas_actuel["total_glucides"]
        self.compare_diff_glucides.setText(f"{diff_gluc:+.1f} g")
        if abs(diff_gluc) < 5:  # Petite différence -> neutre
            self.compare_diff_glucides.setStyleSheet("")
        elif diff_gluc > 0:
            self.compare_diff_glucides.setStyleSheet(
                f"color: {self._get_status_color('medium')}; font-weight: bold;"
            )
        else:
            self.compare_diff_glucides.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )

        # Lipides
        self.compare_current_lipides.setText(f"{repas_actuel['total_lipides']:.1f} g")
        self.compare_new_lipides.setText(f"{repas_nouveau['total_lipides']:.1f} g")

        diff_lip = repas_nouveau["total_lipides"] - repas_actuel["total_lipides"]
        self.compare_diff_lipides.setText(f"{diff_lip:+.1f} g")
        if abs(diff_lip) < 2:  # Petite différence -> neutre
            self.compare_diff_lipides.setStyleSheet("")
        elif diff_lip > 0:
            self.compare_diff_lipides.setStyleSheet(
                f"color: {self._get_status_color('medium')}; font-weight: bold;"
            )
        else:
            self.compare_diff_lipides.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )

        # Fibres
        total_fibres_actuel = sum(
            (a.get("fibres", 0) * a["quantite"] / 100) for a in repas_actuel["aliments"]
        )
        total_fibres_nouveau = sum(
            (a.get("fibres", 0) * a["quantite"] / 100)
            for a in repas_nouveau["aliments"]
        )

        self.compare_current_fibres.setText(f"{total_fibres_actuel:.1f} g")
        self.compare_new_fibres.setText(f"{total_fibres_nouveau:.1f} g")

        diff_fibre = total_fibres_nouveau - total_fibres_actuel
        self.compare_diff_fibres.setText(f"{diff_fibre:+.1f} g")
        if diff_fibre > 0:
            self.compare_diff_fibres.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )
        elif diff_fibre < 0:
            self.compare_diff_fibres.setStyleSheet(
                f"color: {self._get_status_color('over')}; font-weight: bold;"
            )
        else:
            self.compare_diff_fibres.setStyleSheet("")

        # Coût
        total_cout_actuel = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_actuel["aliments"]
        )
        total_cout_nouveau = sum(
            (a.get("prix_kg", 0) * a["quantite"] / 1000)
            for a in repas_nouveau["aliments"]
        )

        self.compare_current_cout.setText(f"{total_cout_actuel:.2f} €")
        self.compare_new_cout.setText(f"{total_cout_nouveau:.2f} €")

        diff_cout = total_cout_nouveau - total_cout_actuel
        self.compare_diff_cout.setText(f"{diff_cout:+.2f} €")
        if diff_cout > 0:
            self.compare_diff_cout.setStyleSheet(
                f"color: {self._get_status_color('over')}; font-weight: bold;"
            )
        elif diff_cout < 0:
            self.compare_diff_cout.setStyleSheet(
                f"color: {self._get_status_color('good')}; font-weight: bold;"
            )
        else:
            self.compare_diff_cout.setStyleSheet("")

        # Mise à jour de l'impact sur la journée si les données sont disponibles
        if totaux_jour:
            # Valeurs actuelles du jour = totaux journaliers actuels
            current_cal = totaux_jour.get("calories", 0) + repas_actuel.get(
                "total_calories", 0
            )
            current_prot = totaux_jour.get("proteines", 0) + repas_actuel.get(
                "total_proteines", 0
            )
            current_gluc = totaux_jour.get("glucides", 0) + repas_actuel.get(
                "total_glucides", 0
            )
            current_lip = totaux_jour.get("lipides", 0) + repas_actuel.get(
                "total_lipides", 0
            )

            # Mise à jour des labels pour les valeurs actuelles (totaux jour)
            self.current_calories.setText(f"{current_cal:.0f} kcal")
            self.current_proteines.setText(f"{current_prot:.1f} g")
            self.current_glucides.setText(f"{current_gluc:.1f} g")
            self.current_lipides.setText(f"{current_lip:.1f} g")

            # Nouvelles valeurs = totaux jour ACTUELS - repas actuel + nouveau repas
            new_cal = (
                current_cal
                - repas_actuel.get("total_calories", 0)
                + repas_nouveau.get("total_calories", 0)
            )
            new_prot = (
                current_prot
                - repas_actuel.get("total_proteines", 0)
                + repas_nouveau.get("total_proteines", 0)
            )
            new_gluc = (
                current_gluc
                - repas_actuel.get("total_glucides", 0)
                + repas_nouveau.get("total_glucides", 0)
            )
            new_lip = (
                current_lip
                - repas_actuel.get("total_lipides", 0)
                + repas_nouveau.get("total_lipides", 0)
            )

            # S'assurer qu'aucune valeur n'est négative
            new_cal = max(0, new_cal)
            new_prot = max(0, new_prot)
            new_gluc = max(0, new_gluc)
            new_lip = max(0, new_lip)

            # Mise à jour des labels pour les nouvelles valeurs
            self.new_calories.setText(f"{new_cal:.0f} kcal")
            self.new_proteines.setText(f"{new_prot:.1f} g")
            self.new_glucides.setText(f"{new_gluc:.1f} g")
            self.new_lipides.setText(f"{new_lip:.1f} g")

            # Récupérer les objectifs de l'utilisateur
            cal_target = self.user_cal_target
            prot_target = self.user_prot_target
            gluc_target = self.user_gluc_target
            lip_target = self.user_lip_target

            # Mettre à jour les objectifs affichés
            self.target_calories.setText(f"{cal_target} kcal")
            self.target_proteines.setText(f"{prot_target} g")
            self.target_glucides.setText(f"{gluc_target} g")
            self.target_lipides.setText(f"{lip_target} g")

            # Calculer et afficher les pourcentages des objectifs (actuels)
            current_cal_percent = min(
                round((current_cal / cal_target) * 100 if cal_target else 0), 999
            )
            current_prot_percent = min(
                round((current_prot / prot_target) * 100 if prot_target else 0), 999
            )
            current_gluc_percent = min(
                round((current_gluc / gluc_target) * 100 if gluc_target else 0), 999
            )
            current_lip_percent = min(
                round((current_lip / lip_target) * 100 if lip_target else 0), 999
            )

            # Moyenne des pourcentages actuels
            current_avg_percent = round(
                (
                    current_cal_percent
                    + current_prot_percent
                    + current_gluc_percent
                    + current_lip_percent
                )
                / 4
            )

            # Pourcentages des nouvelles valeurs
            new_cal_percent = min(
                round((new_cal / cal_target) * 100 if cal_target else 0), 999
            )
            new_prot_percent = min(
                round((new_prot / prot_target) * 100 if prot_target else 0), 999
            )
            new_gluc_percent = min(
                round((new_gluc / gluc_target) * 100 if gluc_target else 0), 999
            )
            new_lip_percent = min(
                round((new_lip / lip_target) * 100 if lip_target else 0), 999
            )

            # Moyenne des nouveaux pourcentages
            new_avg_percent = round(
                (
                    new_cal_percent
                    + new_prot_percent
                    + new_gluc_percent
                    + new_lip_percent
                )
                / 4
            )

            # Afficher les pourcentages
            self.percent_current.setText(
                f"Cal: {current_cal_percent}% / Moy: {current_avg_percent}%"
            )
            self.percent_new.setText(
                f"Cal: {new_cal_percent}% / Moy: {new_avg_percent}%"
            )

            # Appliquer une couleur en fonction du rapport à l'objectif
            self._apply_target_color_to_label(
                self.current_calories, current_cal, cal_target
            )
            self._apply_target_color_to_label(
                self.current_proteines, current_prot, prot_target
            )
            self._apply_target_color_to_label(
                self.current_glucides, current_gluc, gluc_target
            )
            self._apply_target_color_to_label(
                self.current_lipides, current_lip, lip_target
            )

            self._apply_target_color_to_label(self.new_calories, new_cal, cal_target)
            self._apply_target_color_to_label(self.new_proteines, new_prot, prot_target)
            self._apply_target_color_to_label(self.new_glucides, new_gluc, gluc_target)
            self._apply_target_color_to_label(self.new_lipides, new_lip, lip_target)

    def _apply_target_color_to_label(self, label, value, target):
        """Applique une couleur au label en fonction du rapport à l'objectif"""
        if target <= 0:  # Éviter division par zéro
            return

        ratio = value / target
        percentage = ratio  # Conservation du ratio pour le calcul du pourcentage

        # Définir le statut basé sur le pourcentage (même logique que les barres de progression)
        if percentage > 1.05:
            status = "over"  # Rouge - trop élevé
        elif 0.95 <= percentage <= 1.05:
            status = "good"  # Vert - idéal
        elif 0.5 <= percentage < 0.95:
            status = "medium"  # Orange - moyen
        else:
            status = "low"  # Gris - trop bas

        # Stocker le statut comme propriété du label pour pouvoir y accéder via CSS
        label.setProperty("status", status)

        # Appliquer le style selon le statut en utilisant la méthode _get_status_color
        color = self._get_status_color(status)
        label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Définir le texte du tooltip selon le statut
        message = {
            "over": "Excessif",
            "good": "Optimal",
            "medium": "Proche",
            "low": "Insuffisant",
        }
        label.setToolTip(f"{message.get(status, '')}: {ratio*100:.0f}% de l'objectif")
