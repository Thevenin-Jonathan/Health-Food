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
)
from PySide6.QtCore import Qt, QMargins, Signal
from PySide6.QtGui import QFont, QColor

from .tab_base import TabBase


class UtilisateurTab(TabBase):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.setup_ui()
        self.charger_donnees_utilisateur()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)

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
        self.age_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Âge:", self.age_spin)

        self.taille_spin = QDoubleSpinBox()
        self.taille_spin.setRange(100, 220)
        self.taille_spin.setValue(175)
        self.taille_spin.setSuffix(" cm")
        self.taille_spin.setDecimals(1)
        self.taille_spin.setSingleStep(0.5)
        self.taille_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Taille:", self.taille_spin)

        self.poids_spin = QDoubleSpinBox()
        self.poids_spin.setRange(30, 200)
        self.poids_spin.setValue(70)
        self.poids_spin.setSuffix(" kg")
        self.poids_spin.setDecimals(1)
        self.poids_spin.setSingleStep(0.1)
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

        # Groupe des objectifs
        objectif_group = QGroupBox("Objectifs")
        objectif_layout = QFormLayout()

        self.objectif_combo = QComboBox()
        self.objectif_combo.addItems(["Maintien", "Perte de poids", "Prise de masse"])
        self.objectif_combo.currentIndexChanged.connect(self.on_objectif_changed)
        objectif_layout.addRow("Objectif:", self.objectif_combo)

        variation_layout = QHBoxLayout()
        self.variation_spin = QDoubleSpinBox()
        self.variation_spin.setRange(0, 10)
        self.variation_spin.setValue(5)
        self.variation_spin.setDecimals(1)
        self.variation_spin.setSingleStep(0.1)
        self.variation_spin.setSuffix(" g/100g/semaine")
        self.variation_spin.setEnabled(False)
        self.variation_spin.valueChanged.connect(self.calculer_calories)
        variation_layout.addWidget(self.variation_spin)
        variation_layout.addStretch()

        self.variation_label = QLabel("≈ 0 kcal/jour")
        variation_layout.addWidget(self.variation_label)

        objectif_layout.addRow("Variation:", variation_layout)

        # Calorie personnalisées
        custom_cal_layout = QHBoxLayout()
        self.custom_calories_spin = QSpinBox()
        self.custom_calories_spin.setRange(0, 10000)
        self.custom_calories_spin.setValue(0)
        self.custom_calories_spin.setSuffix(" kcal")
        self.custom_calories_spin.setSpecialValueText("Auto (calculé)")
        self.custom_calories_spin.valueChanged.connect(self.calculer_calories)
        custom_cal_layout.addWidget(self.custom_calories_spin)

        objectif_layout.addRow("Calories personnalisées:", custom_cal_layout)

        objectif_group.setLayout(objectif_layout)
        right_column.addWidget(objectif_group)

        # Groupe de la répartition des macros
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

        # Sliders pour les pourcentages
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

        return {
            "label": label,
            "slider": slider,
            "value_label": value_label,
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

        # Si le total n'est pas 100%, ajuster le dernier slider modifié
        if total != 100:
            # Déterminer quel slider a été modifié (celui qui a le focus)
            sender = self.sender()

            if sender == self.proteines_slider["slider"]:
                # Ajuster les glucides et lipides proportionnellement
                if g_val + l_val > 0:
                    ratio = (100 - p_val) / (g_val + l_val)
                    new_g = int(g_val * ratio)
                    new_l = 100 - p_val - new_g

                    # Bloquer temporairement les signaux pour éviter les boucles
                    self.glucides_slider["slider"].blockSignals(True)
                    self.lipides_slider["slider"].blockSignals(True)

                    self.glucides_slider["slider"].setValue(new_g)
                    self.lipides_slider["slider"].setValue(new_l)

                    self.glucides_slider["slider"].blockSignals(False)
                    self.lipides_slider["slider"].blockSignals(False)
                else:
                    # Si les deux autres sont à 0, mettre le reste dans glucides
                    self.glucides_slider["slider"].setValue(100 - p_val)

            elif sender == self.glucides_slider["slider"]:
                # Ajuster les protéines et lipides proportionnellement
                if p_val + l_val > 0:
                    ratio = (100 - g_val) / (p_val + l_val)
                    new_p = int(p_val * ratio)
                    new_l = 100 - g_val - new_p

                    # Bloquer temporairement les signaux pour éviter les boucles
                    self.proteines_slider["slider"].blockSignals(True)
                    self.lipides_slider["slider"].blockSignals(True)

                    self.proteines_slider["slider"].setValue(new_p)
                    self.lipides_slider["slider"].setValue(new_l)

                    self.proteines_slider["slider"].blockSignals(False)
                    self.lipides_slider["slider"].blockSignals(False)
                else:
                    # Si les deux autres sont à 0, mettre le reste dans lipides
                    self.lipides_slider["slider"].setValue(100 - g_val)

            else:  # Lipides slider
                # Ajuster les protéines et glucides proportionnellement
                if p_val + g_val > 0:
                    ratio = (100 - l_val) / (p_val + g_val)
                    new_p = int(p_val * ratio)
                    new_g = 100 - l_val - new_p

                    # Bloquer temporairement les signaux pour éviter les boucles
                    self.proteines_slider["slider"].blockSignals(True)
                    self.glucides_slider["slider"].blockSignals(True)

                    self.proteines_slider["slider"].setValue(new_p)
                    self.glucides_slider["slider"].setValue(new_g)

                    self.proteines_slider["slider"].blockSignals(False)
                    self.glucides_slider["slider"].blockSignals(False)
                else:
                    # Si les deux autres sont à 0, mettre le reste dans protéines
                    self.proteines_slider["slider"].setValue(100 - l_val)

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

        # Activer les sliders uniquement en mode personnalisé
        is_custom = preset == "Personnalisé"
        self.proteines_slider["slider"].setEnabled(is_custom)
        self.glucides_slider["slider"].setEnabled(is_custom)
        self.lipides_slider["slider"].setEnabled(is_custom)

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
        self.variation_spin.setValue(user_data.get("taux_variation", 5))
        self.variation_spin.setEnabled(
            user_data.get("objectif", "Maintien") != "Maintien"
        )

        # Calories personnalisées
        self.custom_calories_spin.setValue(user_data.get("calories_personnalisees", 0))

        # Répartition des macros
        self.macro_combo.setCurrentText(user_data.get("repartition_macros", "Standard"))
        is_custom = user_data.get("repartition_macros", "Standard") == "Personnalisé"
        self.proteines_slider["slider"].setEnabled(is_custom)
        self.glucides_slider["slider"].setEnabled(is_custom)
        self.lipides_slider["slider"].setEnabled(is_custom)

        # Calculer les calories
        self.calculer_calories()

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
            "taux_variation": self.variation_spin.value(),
            "calories_personnalisees": self.custom_calories_spin.value(),
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

        # Réinitialiser le bouton après un délai (dans une application réelle, utiliser QTimer)
        # QTimer.singleShot(2000, self.reset_save_button)

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
            "taux_variation": self.variation_spin.value(),
            "calories_personnalisees": self.custom_calories_spin.value(),
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
        taux = self.variation_spin.value()

        if objectif == "Perte de poids":
            # Convertir g/semaine en déficit calorique journalier
            # 1 kg de graisse = environ 7700 kcal
            deficit = round((taux * 7700) / (7 * 100))
            self.variation_label.setText(f"≈ -{deficit} kcal/jour")
        elif objectif == "Prise de masse":
            surplus = round((taux * 7700) / (7 * 100))
            self.variation_label.setText(f"≈ +{surplus} kcal/jour")
        else:
            self.variation_label.setText("≈ 0 kcal/jour")

    def refresh_data(self):
        """Implémentation de la méthode de base pour actualiser les données"""
        self.charger_donnees_utilisateur()
