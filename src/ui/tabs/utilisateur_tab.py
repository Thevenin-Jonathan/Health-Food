from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QGroupBox,
    QRadioButton,
    QSlider,
    QGridLayout,
    QButtonGroup,
    QWidget,
    QStackedWidget,
    QAbstractSpinBox,
)
from PySide6.QtCore import Qt, QMargins, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from .tab_base import TabBase


class UtilisateurTab(TabBase):
    # Style pour les spin boxes - flèches verticales simples
    spin_style = """
            QSpinBox, QDoubleSpinBox {
                padding-right: 5px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 15px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 15px;
            }
        """

    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.setup_ui()
        self.charger_donnees_utilisateur()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

        # Style minimal pour les boutons radio
        radio_style = """
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid #6ab04c;
            background-color: white;
        }

        QRadioButton::indicator:checked {
            background-color: #6ab04c;
            border: 2px solid #6ab04c;
        }

        QRadioButton::indicator:checked {
            image: url(src/ui/icons/checkmark.svg);
            background-color: #6ab04c;
        }

        QRadioButton {
            spacing: 5px;
        }
        """

        # Titre
        title = QLabel("<h1>Profil Utilisateur</h1>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Configurez votre profil pour calculer vos besoins caloriques journaliers"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc)

        # Formulaire principal divisé en deux colonnes
        form_layout = QHBoxLayout()

        # Colonne de gauche: Informations personnelles
        left_column = QVBoxLayout()

        # Groupe des informations personnelles
        personal_group = QGroupBox("Informations personnelles")
        personal_layout = QFormLayout()

        self.nom_edit = QLineEdit()
        personal_layout.addRow("Nom:", self.nom_edit)

        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(["Homme", "Femme"])
        self.sexe_combo.currentIndexChanged.connect(self.calculer_calories)
        personal_layout.addRow("Sexe:", self.sexe_combo)

        self.age_spin = QSpinBox()
        self.age_spin.setRange(15, 100)
        self.age_spin.setValue(30)
        self.age_spin.setStyleSheet(self.spin_style)
        self.age_spin.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        self.age_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Âge:", self.age_spin)

        self.taille_spin = QDoubleSpinBox()
        self.taille_spin.setRange(100, 220)
        self.taille_spin.setValue(175)
        self.taille_spin.setSuffix(" cm")
        self.taille_spin.setDecimals(1)
        self.taille_spin.setSingleStep(0.5)
        self.taille_spin.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        # Style pour améliorer les boutons up/down
        self.taille_spin.setStyleSheet(self.spin_style)
        self.taille_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Taille:", self.taille_spin)

        self.poids_spin = QDoubleSpinBox()
        self.poids_spin.setRange(30, 200)
        self.poids_spin.setValue(70)
        self.poids_spin.setSuffix(" kg")
        self.poids_spin.setDecimals(1)
        self.poids_spin.setSingleStep(0.1)
        self.poids_spin.setStyleSheet(self.spin_style)
        self.poids_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.poids_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Poids:", self.poids_spin)

        personal_group.setLayout(personal_layout)
        left_column.addWidget(personal_group)

        # Groupe du niveau d'activité
        activity_group = QGroupBox("Niveau d'activité physique")
        activity_layout = QFormLayout()

        self.activite_combo = QComboBox()
        self.activite_combo.addItems(
            [
                "Très sédentaire",
                "Sédentaire",
                "Légèrement actif",
                "Peu actif",
                "Modéré",
                "Actif",
                "Très actif",
                "Extrêmement actif",
            ]
        )
        self.activite_combo.setCurrentText("Modéré")
        self.activite_combo.currentIndexChanged.connect(self.calculer_calories)

        activity_description = QLabel(
            "Très sédentaire: Peu ou pas d'exercice, travail de bureau\n"
            "Sédentaire: Exercice léger 1 fois/semaine\n"
            "Légèrement actif: Exercice léger 2 fois/semaine\n"
            "Peu actif: Exercice modéré 3 fois/semaine\n"
            "Modéré: Exercice modéré 4 fois/semaine\n"
            "Actif: Exercice intense 5 fois/semaine\n"
            "Très actif: Exercice intense 6 fois/semaine\n"
            "Extrêmement actif: Exercice très intense quotidien ou métier physique"
        )
        activity_description.setWordWrap(True)

        activity_layout.addRow("Activité:", self.activite_combo)
        activity_layout.addRow(activity_description)

        activity_group.setLayout(activity_layout)
        left_column.addWidget(activity_group)

        # Bouton de sauvegarde
        self.save_button = QPushButton("Sauvegarder le profil")
        self.save_button.clicked.connect(self.sauvegarder_profil)
        left_column.addWidget(self.save_button)

        form_layout.addLayout(left_column)

        # Colonne de droite: Objectifs et calculs
        right_column = QVBoxLayout()

        # Sélection du mode de calcul (nouveau)
        mode_group = QGroupBox("Mode de calcul")
        mode_layout = QHBoxLayout()

        self.mode_auto_radio = QRadioButton("Calcul automatique")
        self.mode_auto_radio.setChecked(True)
        self.mode_auto_radio.setStyleSheet(radio_style)

        self.mode_manuel_radio = QRadioButton("Entrée manuelle")
        self.mode_manuel_radio.setStyleSheet(radio_style)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_auto_radio, 0)
        self.mode_group.addButton(self.mode_manuel_radio, 1)
        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        mode_layout.addWidget(self.mode_auto_radio)
        mode_layout.addWidget(self.mode_manuel_radio)
        mode_group.setLayout(mode_layout)
        right_column.addWidget(mode_group)

        # Widget empilé pour les deux modes
        self.stacked_widget = QStackedWidget()

        # Page 1: Mode automatique
        auto_widget = QWidget()
        auto_layout = QVBoxLayout(auto_widget)

        # Groupe des objectifs (mode auto)
        objectif_group_auto = QGroupBox("Objectifs")
        objectif_layout_auto = QFormLayout()

        self.objectif_combo = QComboBox()
        self.objectif_combo.addItems(["Maintien", "Perte de poids", "Prise de masse"])
        self.objectif_combo.currentIndexChanged.connect(self.on_objectif_changed)
        objectif_layout_auto.addRow("Objectif:", self.objectif_combo)

        # Nouveau champ de variation en g/semaine
        variation_layout = QHBoxLayout()
        self.variation_spin = QSpinBox()
        self.variation_spin.setRange(0, 2000)  # 0 à 2kg par semaine
        self.variation_spin.setValue(500)  # 500g par défaut
        self.variation_spin.setSingleStep(100)  # Pas de 100g
        self.variation_spin.setSuffix(" g/semaine")
        self.variation_spin.setEnabled(False)
        self.variation_spin.setStyleSheet(self.spin_style)
        self.variation_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.variation_spin.valueChanged.connect(self.calculer_calories)
        variation_layout.addWidget(self.variation_spin)
        variation_layout.addStretch()

        self.variation_label = QLabel("≈ 0 kcal/jour")
        variation_layout.addWidget(self.variation_label)

        objectif_layout_auto.addRow(
            "Perte de poids cible à la semaine :", variation_layout
        )
        objectif_group_auto.setLayout(objectif_layout_auto)
        auto_layout.addWidget(objectif_group_auto)

        # Ajouter le widget auto au stacked widget
        self.stacked_widget.addWidget(auto_widget)

        # Page 2: Mode manuel
        manuel_widget = QWidget()
        manuel_layout = QVBoxLayout(manuel_widget)

        # Groupe des calories manuelles
        calories_group = QGroupBox("Calories personnalisées")
        calories_layout = QFormLayout()

        self.calories_manuelles_spin = QSpinBox()
        self.calories_manuelles_spin.setRange(500, 10000)
        self.calories_manuelles_spin.setValue(2000)
        self.calories_manuelles_spin.setSuffix(" kcal")
        self.calories_manuelles_spin.setSingleStep(50)
        self.calories_manuelles_spin.setStyleSheet(self.spin_style)
        self.calories_manuelles_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.calories_manuelles_spin.valueChanged.connect(self.calculer_calories)
        calories_layout.addRow("Calories journalières:", self.calories_manuelles_spin)

        calories_group.setLayout(calories_layout)
        manuel_layout.addWidget(calories_group)

        # Ajouter le widget manuel au stacked widget
        self.stacked_widget.addWidget(manuel_widget)

        # Ajouter le stacked widget à la colonne de droite
        right_column.addWidget(self.stacked_widget)

        # Groupe de la répartition des macros (commun aux deux modes)
        macros_group = QGroupBox("Répartition des macronutriments")
        macros_layout = QVBoxLayout()

        # Préréglages
        presets_layout = QFormLayout()
        self.macro_combo = QComboBox()
        self.macro_combo.addItems(
            [
                "Standard",
                "Low-carb",
                "Hyperprotéiné",
                "Faible en gras",
                "Cétogène",
                "Personnalisé",
            ]
        )
        self.macro_combo.currentIndexChanged.connect(self.on_macro_preset_changed)
        presets_layout.addRow("Préréglage:", self.macro_combo)
        macros_layout.addLayout(presets_layout)

        # Sliders pour les pourcentages avec champs de saisie en grammes
        self.proteines_slider = self.create_macro_slider("Protéines", 30)
        self.glucides_slider = self.create_macro_slider("Glucides", 40)
        self.lipides_slider = self.create_macro_slider("Lipides", 30)

        macros_layout.addLayout(self.proteines_slider["layout"])
        macros_layout.addLayout(self.glucides_slider["layout"])
        macros_layout.addLayout(self.lipides_slider["layout"])

        macros_group.setLayout(macros_layout)
        right_column.addWidget(macros_group)

        # Groupe des résultats
        results_group = QGroupBox("Résultats")
        results_layout = QGridLayout()

        # Métabolisme de base
        self.mb_label = QLabel("0")
        self.mb_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        results_layout.addWidget(QLabel("Métabolisme de base:"), 0, 0)
        results_layout.addWidget(self.mb_label, 0, 1)
        results_layout.addWidget(QLabel("kcal"), 0, 2)

        # Calories pour maintien
        self.maintien_label = QLabel("0")
        self.maintien_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        results_layout.addWidget(QLabel("Calories maintien:"), 1, 0)
        results_layout.addWidget(self.maintien_label, 1, 1)
        results_layout.addWidget(QLabel("kcal"), 1, 2)

        # Calories objectif
        self.objectif_label = QLabel("0")
        self.objectif_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #2e7d32;"
        )
        results_layout.addWidget(QLabel("Calories objectif:"), 2, 0)
        results_layout.addWidget(self.objectif_label, 2, 1)
        results_layout.addWidget(QLabel("kcal"), 2, 2)

        # Macros en grammes et pourcentages
        self.proteines_g_label = QLabel("0 g")
        self.proteines_g_label.setStyleSheet("font-weight: bold;")
        self.proteines_pct_label = QLabel("(30%)")
        results_layout.addWidget(QLabel("Protéines:"), 3, 0)
        results_layout.addWidget(self.proteines_g_label, 3, 1)
        results_layout.addWidget(self.proteines_pct_label, 3, 2)

        self.glucides_g_label = QLabel("0 g")
        self.glucides_g_label.setStyleSheet("font-weight: bold;")
        self.glucides_pct_label = QLabel("(40%)")
        results_layout.addWidget(QLabel("Glucides:"), 4, 0)
        results_layout.addWidget(self.glucides_g_label, 4, 1)
        results_layout.addWidget(self.glucides_pct_label, 4, 2)

        self.lipides_g_label = QLabel("0 g")
        self.lipides_g_label.setStyleSheet("font-weight: bold;")
        self.lipides_pct_label = QLabel("(30%)")
        results_layout.addWidget(QLabel("Lipides:"), 5, 0)
        results_layout.addWidget(self.lipides_g_label, 5, 1)
        results_layout.addWidget(self.lipides_pct_label, 5, 2)

        results_group.setLayout(results_layout)
        right_column.addWidget(results_group)

        form_layout.addLayout(right_column)
        main_layout.addLayout(form_layout)

        # Ajouter des explications/notes
        notes = QLabel(
            "Note: Ces calculs sont basés sur la formule de Harris-Benedict révisée. "
            "Les résultats sont des estimations et peuvent varier selon les individus. "
            "Ajustez vos apports en fonction de vos résultats réels."
        )
        notes.setWordWrap(True)
        notes.setStyleSheet("font-style: italic; color: #666;")
        main_layout.addWidget(notes)

        self.setLayout(main_layout)

        # Initialiser l'état des champs selon le mode
        self.on_mode_changed()

    def create_macro_slider(self, name, default_value):
        """Crée un slider pour les macronutriments avec son label et sa valeur"""
        layout = QHBoxLayout()

        # Label du macronutriment
        label = QLabel(f"{name}:")
        layout.addWidget(label)

        # Slider pour le pourcentage
        slider = QSlider(Qt.Horizontal)
        slider.setRange(5, 70)
        slider.setValue(default_value)
        slider.setEnabled(
            False
        )  # Désactivé par défaut, activé seulement en mode personnalisé
        slider.valueChanged.connect(self.on_macro_slider_changed)
        layout.addWidget(slider)

        # Label de pourcentage
        value_label = QLabel(f"{default_value}%")
        layout.addWidget(value_label)

        # Champ pour saisie directe en grammes
        gram_spin = QSpinBox()
        gram_spin.setRange(0, 500)
        gram_spin.setValue(0)  # Sera mis à jour lors du calcul
        gram_spin.setSuffix(" g")
        gram_spin.setEnabled(False)  # Désactivé par défaut
        gram_spin.setStyleSheet(self.spin_style)
        gram_spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        gram_spin.valueChanged.connect(lambda: self.on_macro_gram_changed(name))
        layout.addWidget(gram_spin)

        return {
            "label": label,
            "slider": slider,
            "value_label": value_label,
            "gram_spin": gram_spin,
            "layout": layout,
        }

    def on_macro_slider_changed(self):
        """Appelé quand un slider de macro est modifié pour s'assurer que le total est de 100%"""
        # Récupérer les valeurs actuelles
        p_val = self.proteines_slider["slider"].value()
        g_val = self.glucides_slider["slider"].value()
        l_val = self.lipides_slider["slider"].value()

        # Calculer le total
        total = p_val + g_val + l_val

        # Si le total n'est pas 100%, ajuster selon le slider modifié
        if total != 100:
            # Déterminer quel slider a été modifié
            sender = self.sender()

            if sender == self.proteines_slider["slider"]:
                # Ajuster uniquement les glucides
                new_g = 100 - p_val - l_val
                if new_g < 5:  # Respecter la valeur minimale
                    new_g = 5
                    new_p = 100 - new_g - l_val
                    if new_p < 5:  # Si impossible, ajuster les lipides aussi
                        new_p = 5
                        new_l = 100 - new_p - new_g
                        self.lipides_slider["slider"].blockSignals(True)
                        self.lipides_slider["slider"].setValue(new_l)
                        self.lipides_slider["slider"].blockSignals(False)
                    self.proteines_slider["slider"].blockSignals(True)
                    self.proteines_slider["slider"].setValue(new_p)
                    self.proteines_slider["slider"].blockSignals(False)

                self.glucides_slider["slider"].blockSignals(True)
                self.glucides_slider["slider"].setValue(new_g)
                self.glucides_slider["slider"].blockSignals(False)

            elif sender == self.lipides_slider["slider"]:
                # Ajuster uniquement les glucides
                new_g = 100 - p_val - l_val
                if new_g < 5:  # Respecter la valeur minimale
                    new_g = 5
                    new_l = 100 - p_val - new_g
                    if new_l < 5:  # Si impossible, ajuster les protéines aussi
                        new_l = 5
                        new_p = 100 - new_l - new_g
                        self.proteines_slider["slider"].blockSignals(True)
                        self.proteines_slider["slider"].setValue(new_p)
                        self.proteines_slider["slider"].blockSignals(False)
                    self.lipides_slider["slider"].blockSignals(True)
                    self.lipides_slider["slider"].setValue(new_l)
                    self.lipides_slider["slider"].blockSignals(False)

                self.glucides_slider["slider"].blockSignals(True)
                self.glucides_slider["slider"].setValue(new_g)
                self.glucides_slider["slider"].blockSignals(False)

            elif sender == self.glucides_slider["slider"]:
                # Ajuster uniquement les protéines
                new_p = 100 - g_val - l_val
                if new_p < 5:  # Respecter la valeur minimale
                    new_p = 5
                    new_g = 100 - new_p - l_val
                    if new_g < 5:  # Si impossible, ajuster les lipides aussi
                        new_g = 5
                        new_l = 100 - new_p - new_g
                        self.lipides_slider["slider"].blockSignals(True)
                        self.lipides_slider["slider"].setValue(new_l)
                        self.lipides_slider["slider"].blockSignals(False)
                    self.glucides_slider["slider"].blockSignals(True)
                    self.glucides_slider["slider"].setValue(new_g)
                    self.glucides_slider["slider"].blockSignals(False)

                self.proteines_slider["slider"].blockSignals(True)
                self.proteines_slider["slider"].setValue(new_p)
                self.proteines_slider["slider"].blockSignals(False)

        # Mettre à jour les labels
        self.proteines_slider["value_label"].setText(
            f"{self.proteines_slider['slider'].value()}%"
        )
        self.glucides_slider["value_label"].setText(
            f"{self.glucides_slider['slider'].value()}%"
        )
        self.lipides_slider["value_label"].setText(
            f"{self.lipides_slider['slider'].value()}%"
        )

        # Recalculer les calories et mettre à jour les champs en grammes
        self.calculer_calories()
        self.update_macro_grams_from_pct()

    def on_macro_gram_changed(self, macro_name):
        """Appelé quand un champ de grammes est modifié pour mettre à jour les pourcentages"""
        # Récupérer les valeurs en grammes
        p_gram = self.proteines_slider["gram_spin"].value()
        g_gram = self.glucides_slider["gram_spin"].value()
        l_gram = self.lipides_slider["gram_spin"].value()

        # Calculer les calories totales des macros
        total_calories = (p_gram * 4) + (g_gram * 4) + (l_gram * 9)

        if total_calories > 0:
            # Calculer les nouveaux pourcentages
            p_pct = int((p_gram * 4 / total_calories) * 100)
            g_pct = int((g_gram * 4 / total_calories) * 100)
            l_pct = int((l_gram * 9 / total_calories) * 100)

            # Ajuster pour s'assurer que le total est 100%
            total_pct = p_pct + g_pct + l_pct
            if total_pct != 100:
                # Ajuster selon le macro modifié
                if macro_name == "Protéines":
                    g_pct = 100 - p_pct - l_pct
                elif macro_name == "Lipides":
                    g_pct = 100 - p_pct - l_pct
                elif macro_name == "Glucides":
                    p_pct = 100 - g_pct - l_pct

            # Mettre à jour les sliders
            self.update_macro_sliders(p_pct, g_pct, l_pct)

            # Mettre à jour les calories objectif
            if self.mode_manuel_radio.isChecked():
                self.calories_manuelles_spin.setValue(int(total_calories))

            # Recalculer pour mettre à jour l'interface
            self.calculer_calories()

    def update_macro_grams_from_pct(self):
        """Met à jour les champs de grammes en fonction des pourcentages et des calories totales"""
        # Récupérer les calories totales
        if self.mode_auto_radio.isChecked():
            calories = int(self.objectif_label.text())
        else:
            calories = self.calories_manuelles_spin.value()

        # Récupérer les pourcentages
        p_pct = self.proteines_slider["slider"].value() / 100
        g_pct = self.glucides_slider["slider"].value() / 100
        l_pct = self.lipides_slider["slider"].value() / 100

        # Calculer les grammes
        p_gram = int((calories * p_pct) / 4)  # 4 kcal par gramme de protéines
        g_gram = int((calories * g_pct) / 4)  # 4 kcal par gramme de glucides
        l_gram = int((calories * l_pct) / 9)  # 9 kcal par gramme de lipides

        # Mettre à jour les champs sans déclencher les signaux
        self.proteines_slider["gram_spin"].blockSignals(True)
        self.glucides_slider["gram_spin"].blockSignals(True)
        self.lipides_slider["gram_spin"].blockSignals(True)

        self.proteines_slider["gram_spin"].setValue(p_gram)
        self.glucides_slider["gram_spin"].setValue(g_gram)
        self.lipides_slider["gram_spin"].setValue(l_gram)

        self.proteines_slider["gram_spin"].blockSignals(False)
        self.glucides_slider["gram_spin"].blockSignals(False)
        self.lipides_slider["gram_spin"].blockSignals(False)

    def on_mode_changed(self, button=None):
        """Gère le changement de mode (auto/manuel)"""
        is_auto = self.mode_auto_radio.isChecked()

        # Changer la page du stacked widget
        self.stacked_widget.setCurrentIndex(0 if is_auto else 1)

        # Activer/désactiver les champs de grammes selon le mode
        is_custom = self.macro_combo.currentText() == "Personnalisé"
        self.proteines_slider["gram_spin"].setEnabled(is_custom)
        self.glucides_slider["gram_spin"].setEnabled(is_custom)
        self.lipides_slider["gram_spin"].setEnabled(is_custom)

        # Recalculer les calories
        self.calculer_calories()

    def on_objectif_changed(self):
        """Gère l'activation/désactivation du champ de variation selon l'objectif"""
        objectif = self.objectif_combo.currentText()
        self.variation_spin.setEnabled(objectif != "Maintien")
        self.calculer_calories()

    def on_macro_preset_changed(self):
        """Gère le changement de préréglage des macros"""
        preset = self.macro_combo.currentText()

        # Activer les sliders et les champs de grammes uniquement en mode personnalisé
        is_custom = preset == "Personnalisé"
        self.proteines_slider["slider"].setEnabled(is_custom)
        self.glucides_slider["slider"].setEnabled(is_custom)
        self.lipides_slider["slider"].setEnabled(is_custom)
        self.proteines_slider["gram_spin"].setEnabled(is_custom)
        self.glucides_slider["gram_spin"].setEnabled(is_custom)
        self.lipides_slider["gram_spin"].setEnabled(is_custom)

        # Mettre à jour les valeurs selon le préréglage
        if preset == "Standard":
            self.update_macro_sliders(30, 40, 30)
        elif preset == "Low-carb":
            self.update_macro_sliders(35, 25, 40)
        elif preset == "Hyperprotéiné":
            self.update_macro_sliders(45, 35, 20)
        elif preset == "Faible en gras":
            self.update_macro_sliders(35, 50, 15)
        elif preset == "Cétogène":
            self.update_macro_sliders(30, 5, 65)

        self.calculer_calories()
        self.update_macro_grams_from_pct()

    def update_macro_sliders(self, p, g, l):
        """Met à jour les valeurs des sliders sans déclencher les signaux"""
        self.proteines_slider["slider"].blockSignals(True)
        self.glucides_slider["slider"].blockSignals(True)
        self.lipides_slider["slider"].blockSignals(True)

        self.proteines_slider["slider"].setValue(p)
        self.glucides_slider["slider"].setValue(g)
        self.lipides_slider["slider"].setValue(l)

        self.proteines_slider["value_label"].setText(f"{p}%")
        self.glucides_slider["value_label"].setText(f"{g}%")
        self.lipides_slider["value_label"].setText(f"{l}%")

        self.proteines_slider["slider"].blockSignals(False)
        self.glucides_slider["slider"].blockSignals(False)
        self.lipides_slider["slider"].blockSignals(False)

    def charger_donnees_utilisateur(self):
        """Charge les données de l'utilisateur depuis la base de données"""
        user_data = self.db_manager.get_utilisateur()

        # Remplir les champs du formulaire
        self.nom_edit.setText(user_data.get("nom", ""))
        self.sexe_combo.setCurrentText(user_data.get("sexe", "Homme"))
        self.age_spin.setValue(user_data.get("age", 30))
        self.taille_spin.setValue(user_data.get("taille", 175))
        self.poids_spin.setValue(user_data.get("poids", 70))
        self.activite_combo.setCurrentText(user_data.get("niveau_activite", "Modéré"))

        # Objectifs
        self.objectif_combo.setCurrentText(user_data.get("objectif", "Maintien"))

        # Convertir l'ancienne valeur (g/100g/semaine) en g/semaine
        old_variation = user_data.get("taux_variation", 5)
        new_variation = int(old_variation * 100)  # Convertir en grammes entiers
        self.variation_spin.setValue(new_variation)

        self.variation_spin.setEnabled(
            user_data.get("objectif", "Maintien") != "Maintien"
        )

        # Calories personnalisées
        calories_perso = user_data.get("calories_personnalisees", 0)
        if calories_perso > 0:
            self.mode_manuel_radio.setChecked(True)
            self.calories_manuelles_spin.setValue(calories_perso)
            self.on_mode_changed()
        else:
            self.mode_auto_radio.setChecked(True)
            self.on_mode_changed()

        # Répartition des macros
        self.macro_combo.setCurrentText(user_data.get("repartition_macros", "Standard"))
        is_custom = user_data.get("repartition_macros", "Standard") == "Personnalisé"
        self.proteines_slider["slider"].setEnabled(is_custom)
        self.glucides_slider["slider"].setEnabled(is_custom)
        self.lipides_slider["slider"].setEnabled(is_custom)
        self.proteines_slider["gram_spin"].setEnabled(is_custom)
        self.glucides_slider["gram_spin"].setEnabled(is_custom)
        self.lipides_slider["gram_spin"].setEnabled(is_custom)

        # Calculer les calories
        self.calculer_calories()
        self.update_macro_grams_from_pct()

    def sauvegarder_profil(self):
        """Sauvegarde le profil utilisateur dans la base de données"""
        # Récupérer les valeurs des champs
        user_data = {
            "nom": self.nom_edit.text(),
            "sexe": self.sexe_combo.currentText(),
            "age": self.age_spin.value(),
            "taille": self.taille_spin.value(),
            "poids": self.poids_spin.value(),
            "niveau_activite": self.activite_combo.currentText(),
            "objectif": self.objectif_combo.currentText(),
            "taux_variation": self.variation_spin.value()
            / 100,  # Convertir en g/100g/semaine pour compatibilité
            "calories_personnalisees": (
                self.calories_manuelles_spin.value()
                if self.mode_manuel_radio.isChecked()
                else 0
            ),
            "repartition_macros": self.macro_combo.currentText(),
        }

        # Si répartition personnalisée, stocker les pourcentages des sliders
        if self.macro_combo.currentText() == "Personnalisé":
            user_data["proteines_pct"] = self.proteines_slider["slider"].value() / 100
            user_data["glucides_pct"] = self.glucides_slider["slider"].value() / 100
            user_data["lipides_pct"] = self.lipides_slider["slider"].value() / 100

        # Sauvegarder dans la base de données
        self.db_manager.sauvegarder_utilisateur(user_data)

        # Afficher confirmation
        self.save_button.setText("Profil sauvegardé!")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Réinitialiser le bouton après un délai de 2 secondes
        QTimer.singleShot(2000, self.reset_save_button)

    def reset_save_button(self):
        """Réinitialise l'apparence du bouton de sauvegarde"""
        self.save_button.setText("Sauvegarder le profil")
        self.save_button.setStyleSheet("")

    def calculer_calories(self):
        """Calcule les besoins caloriques et met à jour l'affichage"""
        # Préparer les données utilisateur à partir des champs du formulaire
        user_data = {
            "sexe": self.sexe_combo.currentText(),
            "age": self.age_spin.value(),
            "taille": self.taille_spin.value(),
            "poids": self.poids_spin.value(),
            "niveau_activite": self.activite_combo.currentText(),
            "objectif": self.objectif_combo.currentText(),
            "taux_variation": self.variation_spin.value()
            / 100,  # Convertir en g/100g/semaine pour compatibilité
            "calories_personnalisees": (
                self.calories_manuelles_spin.value()
                if self.mode_manuel_radio.isChecked()
                else 0
            ),
            "repartition_macros": self.macro_combo.currentText(),
        }

        # Si répartition personnalisée, ajouter les pourcentages des sliders
        if self.macro_combo.currentText() == "Personnalisé":
            user_data["proteines_pct"] = self.proteines_slider["slider"].value() / 100
            user_data["glucides_pct"] = self.glucides_slider["slider"].value() / 100
            user_data["lipides_pct"] = self.lipides_slider["slider"].value() / 100

        # Effectuer le calcul
        resultats = self.db_manager.calculer_calories_journalieres(user_data)

        # Mettre à jour l'affichage des résultats
        self.mb_label.setText(str(resultats["metabolisme_base"]))
        self.maintien_label.setText(str(resultats["calories_maintien"]))
        self.objectif_label.setText(str(resultats["calories_finales"]))

        # Macros en grammes et pourcentages
        self.proteines_g_label.setText(f"{resultats['proteines_g']} g")
        self.glucides_g_label.setText(f"{resultats['glucides_g']} g")
        self.lipides_g_label.setText(f"{resultats['lipides_g']} g")

        # Afficher les pourcentages dans les labels
        pct_p = int(resultats["proteines_pct"] * 100)
        pct_g = int(resultats["glucides_pct"] * 100)
        pct_l = int(resultats["lipides_pct"] * 100)

        # Mettre à jour les labels des pourcentages directement
        self.proteines_pct_label.setText(f"({pct_p}%)")
        self.glucides_pct_label.setText(f"({pct_g}%)")
        self.lipides_pct_label.setText(f"({pct_l}%)")

        # Mettre à jour le label de variation
        objectif = self.objectif_combo.currentText()
        taux = self.variation_spin.value()  # En grammes par semaine

        if objectif == "Perte de poids":
            # Convertir g/semaine en déficit calorique journalier
            # 100g de graisse = environ 770 kcal
            deficit = round((taux * 770) / (7 * 100))  # Utiliser 770 kcal pour 100g
            self.variation_label.setText(f"≈ -{deficit} kcal/jour")
        elif objectif == "Prise de masse":
            surplus = round((taux * 770) / (7 * 100))  # Utiliser 770 kcal pour 100g
            self.variation_label.setText(f"≈ +{surplus} kcal/jour")
        else:
            self.variation_label.setText("≈ 0 kcal/jour")

        # Mettre à jour les champs de grammes
        self.update_macro_grams_from_pct()

    def refresh_data(self):
        """Implémentation de la méthode de base pour actualiser les données"""
        self.charger_donnees_utilisateur()
