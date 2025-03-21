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
    QGridLayout,
    QButtonGroup,
    QWidget,
    QStackedWidget,
    QAbstractSpinBox,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer
from src.utils.events import EVENT_BUS
from .tab_base import TabBase


class UtilisateurTab(TabBase):
    # Définitions des régimes alimentaires
    REGIMES = {
        "Régime équilibré": {
            "description": "Maintenir le poids avec une répartition globale équilibrée.",
            "proteines": (1.2, 1.6),  # (min, max) en g/kg
            "glucides": (3.0, 5.0),
            "lipides": (0.8, 1.0),
        },
        "Régime hypocalorique": {
            "description": "Créer un déficit calorique tout en maintenant les muscles.",
            "proteines": (1.6, 2.2),
            "glucides": (1.0, 3.0),
            "lipides": (0.6, 0.8),
        },
        "Régime hyperprotéiné": {
            "description": "Favoriser la prise de muscle ou maximiser la définition musculaire.",
            "proteines": (1.8, 2.5),
            "glucides": (2.0, 4.0),
            "lipides": (0.8, 1.0),
        },
        "Régime cétogène": {
            "description": "Passer en état de cétose (brûler les graisses comme source principale d'énergie).",
            "proteines": (1.2, 1.6),
            "glucides": (0.5, 1.0),
            "lipides": (1.8, 2.5),
        },
        "Régime de prise de masse": {
            "description": "Construire du muscle tout en minimisant le gain de graisse.",
            "proteines": (1.6, 2.2),
            "glucides": (4.0, 6.0),
            "lipides": (0.8, 1.2),
        },
        "Régime végétarien / vegan": {
            "description": "Adapté à une alimentation sans viande (attention à l'apport protéique complet).",
            "proteines": (1.6, 2.2),
            "glucides": (3.0, 5.0),
            "lipides": (0.8, 1.0),
        },
        "Personnalisé": {
            "description": "Définir manuellement vos besoins en macronutriments.",
            "proteines": (1.4, 1.4),  # Valeurs par défaut
            "glucides": (3.0, 3.0),
            "lipides": (0.9, 0.9),
        },
    }

    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.setup_ui()
        self.charger_donnees_utilisateur()

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
        self.age_spin.setProperty("class", "spin-box-vertical")
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
        self.taille_spin.setProperty("class", "spin-box-vertical")
        self.taille_spin.valueChanged.connect(self.calculer_calories)
        personal_layout.addRow("Taille:", self.taille_spin)

        self.poids_spin = QDoubleSpinBox()
        self.poids_spin.setRange(30, 200)
        self.poids_spin.setValue(70)
        self.poids_spin.setSuffix(" kg")
        self.poids_spin.setDecimals(1)
        self.poids_spin.setSingleStep(0.1)
        self.poids_spin.setProperty("class", "spin-box-vertical")
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
        self.save_button.setProperty("class", "saveButton")
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

        self.mode_manuel_radio = QRadioButton("Entrée manuelle")

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
        self.variation_spin.setProperty("class", "spin-box-vertical")
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
        self.calories_manuelles_spin.setProperty("class", "spin-box-vertical")
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

        # Préréglages de régimes
        presets_layout = QFormLayout()
        self.regime_combo = QComboBox()
        self.regime_combo.addItems(self.REGIMES.keys())
        self.regime_combo.currentIndexChanged.connect(self.on_regime_changed)
        presets_layout.addRow("Type de régime:", self.regime_combo)

        # Description du régime
        self.regime_description = QLabel(
            self.REGIMES["Régime équilibré"]["description"]
        )
        self.regime_description.setWordWrap(True)
        self.regime_description.setProperty("class", "hint")
        presets_layout.addRow(self.regime_description)

        macros_layout.addLayout(presets_layout)

        # Ligne de séparation
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        macros_layout.addWidget(line)

        # Table des macronutriments
        macro_table = QGridLayout()
        macro_table.setHorizontalSpacing(15)

        # En-têtes
        macro_table.addWidget(QLabel(""), 0, 0)
        header_g_kg = QLabel("g/kg de poids corporel")
        header_g_kg.setAlignment(Qt.AlignCenter)
        header_g_kg.setProperty("class", "bold")
        macro_table.addWidget(header_g_kg, 0, 1, 1, 2)

        header_total = QLabel("Total (grammes)")
        header_total.setAlignment(Qt.AlignCenter)
        header_total.setProperty("class", "bold")
        macro_table.addWidget(header_total, 0, 3)

        # Protéines
        prot_label = QLabel("Protéines:")
        prot_label.setProperty("class", "bold")
        macro_table.addWidget(prot_label, 1, 0)

        self.prot_min_spin = QDoubleSpinBox()
        self.prot_min_spin.setRange(0.1, 4.0)
        self.prot_min_spin.setDecimals(1)
        self.prot_min_spin.setSingleStep(0.1)
        self.prot_min_spin.setValue(1.2)
        self.prot_min_spin.setProperty("class", "spin-box-vertical")
        self.prot_min_spin.valueChanged.connect(self.calculer_calories)
        macro_table.addWidget(self.prot_min_spin, 1, 1)

        macro_table.addWidget(QLabel("-"), 1, 2, Qt.AlignCenter)

        self.prot_gram_label = QLabel("0 g")
        self.prot_gram_label.setProperty("class", "bold")
        macro_table.addWidget(self.prot_gram_label, 1, 3, Qt.AlignCenter)

        # Glucides
        gluc_label = QLabel("Glucides:")
        gluc_label.setProperty("class", "bold")
        macro_table.addWidget(gluc_label, 2, 0)

        self.gluc_min_spin = QDoubleSpinBox()
        self.gluc_min_spin.setRange(0.1, 8.0)
        self.gluc_min_spin.setDecimals(1)
        self.gluc_min_spin.setSingleStep(0.1)
        self.gluc_min_spin.setValue(3.0)
        self.gluc_min_spin.setProperty("class", "spin-box-vertical")
        self.gluc_min_spin.valueChanged.connect(self.calculer_calories)
        macro_table.addWidget(self.gluc_min_spin, 2, 1)

        macro_table.addWidget(QLabel("-"), 2, 2, Qt.AlignCenter)

        self.gluc_gram_label = QLabel("0 g")
        self.gluc_gram_label.setProperty("class", "bold")
        macro_table.addWidget(self.gluc_gram_label, 2, 3, Qt.AlignCenter)

        # Lipides
        lip_label = QLabel("Lipides:")
        lip_label.setProperty("class", "bold")
        macro_table.addWidget(lip_label, 3, 0)

        self.lip_min_spin = QDoubleSpinBox()
        self.lip_min_spin.setRange(0.1, 3.0)
        self.lip_min_spin.setDecimals(1)
        self.lip_min_spin.setSingleStep(0.1)
        self.lip_min_spin.setValue(0.8)
        self.lip_min_spin.setProperty("class", "spin-box-vertical")
        self.lip_min_spin.valueChanged.connect(self.calculer_calories)
        macro_table.addWidget(self.lip_min_spin, 3, 1)

        macro_table.addWidget(QLabel("-"), 3, 2, Qt.AlignCenter)

        self.lip_gram_label = QLabel("0 g")
        self.lip_gram_label.setProperty("class", "bold")
        macro_table.addWidget(self.lip_gram_label, 3, 3, Qt.AlignCenter)

        macros_layout.addLayout(macro_table)

        macros_group.setLayout(macros_layout)
        right_column.addWidget(macros_group)

        # Groupe des résultats
        results_group = QGroupBox("Résultats")
        results_group.setProperty("class", "important-group")
        results_layout = QGridLayout()

        # Métabolisme de base
        self.mb_label = QLabel("0")
        self.mb_label.setProperty("class", "result-value")
        results_layout.addWidget(QLabel("Métabolisme de base:"), 0, 0)
        results_layout.addWidget(self.mb_label, 0, 1)
        results_layout.addWidget(QLabel("kcal"), 0, 2)

        # Calories pour maintien
        self.maintien_label = QLabel("0")
        self.maintien_label.setProperty("class", "result-value")
        results_layout.addWidget(QLabel("Calories maintien:"), 1, 0)
        results_layout.addWidget(self.maintien_label, 1, 1)
        results_layout.addWidget(QLabel("kcal"), 1, 2)

        # Calories objectif
        self.objectif_label = QLabel("0")
        self.objectif_label.setProperty("class", "result-value-highlight")
        results_layout.addWidget(QLabel("Calories objectif:"), 2, 0)
        results_layout.addWidget(self.objectif_label, 2, 1)
        results_layout.addWidget(QLabel("kcal"), 2, 2)

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
        notes.setProperty("class", "hint-small")
        main_layout.addWidget(notes)

        # Initialiser l'état des champs selon le mode
        self.on_mode_changed()

        # Ajouter le widget de contenu au layout central avec des marges extensibles
        center_layout.addStretch(1)
        center_layout.addWidget(content_widget)
        center_layout.addStretch(1)

        # Ajouter le layout central au layout extérieur
        outer_layout.addLayout(center_layout)

        self.setLayout(outer_layout)

    def on_regime_changed(self):
        """Appelé quand le type de régime alimentaire change"""
        regime_nom = self.regime_combo.currentText()
        regime_data = self.REGIMES[regime_nom]

        # Mettre à jour la description
        self.regime_description.setText(regime_data["description"])

        # Mettre à jour les valeurs des spins
        self.prot_min_spin.setValue(regime_data["proteines"][0])
        self.gluc_min_spin.setValue(regime_data["glucides"][0])
        self.lip_min_spin.setValue(regime_data["lipides"][0])

        # Activer/désactiver la modification selon le régime sélectionné
        is_custom = regime_nom == "Personnalisé"
        self.prot_min_spin.setEnabled(is_custom)
        self.gluc_min_spin.setEnabled(is_custom)
        self.lip_min_spin.setEnabled(is_custom)

        # Recalculer les calories
        self.calculer_calories()

    def on_mode_changed(self):
        """Gère le changement de mode (auto/manuel)"""
        is_auto = self.mode_auto_radio.isChecked()

        # Changer la page du stacked widget
        self.stacked_widget.setCurrentIndex(0 if is_auto else 1)

        # Recalculer les calories
        self.calculer_calories()

    def on_objectif_changed(self):
        """Gère l'activation/désactivation du champ de variation selon l'objectif"""
        objectif = self.objectif_combo.currentText()
        self.variation_spin.setEnabled(objectif != "Maintien")
        self.calculer_calories()

    def update_macro_grams(self):
        """Calcule et ajuste les grammes de macronutriments en fonction du poids, des valeurs g/kg et des calories cibles"""
        poids = self.poids_spin.value()

        # Récupérer les valeurs de base des macros en g/kg selon le régime sélectionné
        regime_nom = self.regime_combo.currentText()

        # Calculer les calories cibles
        if self.mode_auto_radio.isChecked() and self.objectif_label.text():
            calories_cible = int(self.objectif_label.text())
        else:
            calories_cible = self.calories_manuelles_spin.value()

        # Convertir les g/kg en grammes - valeurs de base
        prot_g_kg = self.prot_min_spin.value()
        gluc_g_kg = self.gluc_min_spin.value()
        lip_g_kg = self.lip_min_spin.value()

        # Calculer les grammes de base
        prot_g_base = round(prot_g_kg * poids)
        gluc_g_base = round(gluc_g_kg * poids)
        lip_g_base = round(lip_g_kg * poids)

        # Calculer les calories de base
        cal_prot = prot_g_base * 4  # 4 kcal par gramme de protéines
        cal_gluc = gluc_g_base * 4  # 4 kcal par gramme de glucides
        cal_lip = lip_g_base * 9  # 9 kcal par gramme de lipides

        total_cal_base = cal_prot + cal_gluc + cal_lip

        # Si les calories de base sont différentes des calories cibles, ajuster les macros
        if abs(total_cal_base - calories_cible) > 10:  # Tolérance de 10 kcal
            # 1. Protéines : priorité haute - maintenir ou ajuster légèrement si en excès
            prot_g = prot_g_base

            # 2. Lipides : maintenir un minimum, ajuster si nécessaire
            lip_g = lip_g_base
            lip_g_min = round(0.6 * poids)  # Minimum 0.6g/kg

            # 3. Calculer les glucides comme variable d'ajustement principal
            cal_restantes = calories_cible - (prot_g * 4) - (lip_g * 9)
            gluc_g = max(10, round(cal_restantes / 4))  # Minimum 10g de glucides

            # 4. Si les glucides sont trop bas (<0.5 g/kg) et les lipides/protéines élevés, ajuster
            if gluc_g < round(0.5 * poids) and calories_cible < total_cal_base:
                # Réduction progressive - d'abord les lipides jusqu'au minimum
                if lip_g > lip_g_min:
                    # Calculer la réduction nécessaire en lipides tout en conservant min 0.5g/kg glucides
                    gluc_g_min = round(0.5 * poids)
                    cal_necessaires = gluc_g_min * 4
                    cal_restantes_apres_prot = calories_cible - (prot_g * 4)

                    # Calculer lipides max possible
                    lip_g = min(
                        lip_g, round((cal_restantes_apres_prot - cal_necessaires) / 9)
                    )
                    lip_g = max(lip_g_min, lip_g)  # Ne pas descendre sous le minimum

                    # Recalculer les glucides
                    cal_restantes = calories_cible - (prot_g * 4) - (lip_g * 9)
                    gluc_g = max(gluc_g_min, round(cal_restantes / 4))

                # Si toujours en déficit calorique important, ajuster légèrement les protéines
                cal_actuelles = (prot_g * 4) + (lip_g * 9) + (gluc_g * 4)
                if cal_actuelles < calories_cible * 0.9:  # Si <90% des calories cibles
                    # Ajuster les protéines mais sans descendre sous 1.6g/kg
                    prot_g_min = round(1.6 * poids)
                    prot_g = max(
                        prot_g_min,
                        round((calories_cible - (lip_g * 9) - (gluc_g * 4)) / 4),
                    )

            # 5. Si on dépasse les calories en prise de masse, privilégier les glucides
            if calories_cible > total_cal_base:
                # En prise de masse, on peut privilégier les glucides
                regime = self.objectif_combo.currentText()
                if regime == "Prise de masse":
                    # Maintenir les protéines et lipides aux valeurs de base
                    # Augmenter les glucides pour atteindre l'objectif calorique
                    cal_restantes = calories_cible - (prot_g * 4) - (lip_g * 9)
                    gluc_g = round(cal_restantes / 4)
        else:
            # Garder les valeurs de base si pas besoin d'ajustement
            prot_g = prot_g_base
            gluc_g = gluc_g_base
            lip_g = lip_g_base

        # Mettre à jour les labels
        self.prot_gram_label.setText(f"{prot_g} g")
        self.gluc_gram_label.setText(f"{gluc_g} g")
        self.lip_gram_label.setText(f"{lip_g} g")

        # Calculer le total des calories ajusté
        total_kcal = (prot_g * 4) + (gluc_g * 4) + (lip_g * 9)

        # Calculer et afficher les pourcentages
        pct_prot = round((prot_g * 4 / total_kcal) * 100) if total_kcal > 0 else 0
        pct_gluc = round((gluc_g * 4 / total_kcal) * 100) if total_kcal > 0 else 0
        pct_lip = round((lip_g * 9 / total_kcal) * 100) if total_kcal > 0 else 0

        # Afficher les g/kg effectifs
        prot_g_kg_effectif = round(prot_g / poids, 1)
        gluc_g_kg_effectif = round(gluc_g / poids, 1)
        lip_g_kg_effectif = round(lip_g / poids, 1)

        # Si les valeurs ont été ajustées, mettre à jour les champs g/kg
        if regime_nom == "Personnalisé" or abs(total_cal_base - total_kcal) > 10:
            self.prot_min_spin.blockSignals(True)
            self.gluc_min_spin.blockSignals(True)
            self.lip_min_spin.blockSignals(True)

            self.prot_min_spin.setValue(prot_g_kg_effectif)
            self.gluc_min_spin.setValue(gluc_g_kg_effectif)
            self.lip_min_spin.setValue(lip_g_kg_effectif)

            self.prot_min_spin.blockSignals(False)
            self.gluc_min_spin.blockSignals(False)
            self.lip_min_spin.blockSignals(False)

        return {
            "proteines_g": prot_g,
            "glucides_g": gluc_g,
            "lipides_g": lip_g,
            "total_kcal": total_kcal,
            "proteines_pct": pct_prot / 100,
            "glucides_pct": pct_gluc / 100,
            "lipides_pct": pct_lip / 100,
        }

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
            "calories_personnalisees": (
                self.calories_manuelles_spin.value()
                if self.mode_manuel_radio.isChecked()
                else 0
            ),
            "regime_alimentaire": self.regime_combo.currentText(),
            "proteines_g_kg": self.prot_min_spin.value(),
            "glucides_g_kg": self.gluc_min_spin.value(),
            "lipides_g_kg": self.lip_min_spin.value(),
        }

        # Effectuer le calcul
        resultats = self.db_manager.calculer_calories_journalieres(user_data)

        # Mettre à jour l'affichage des résultats
        self.mb_label.setText(str(resultats["metabolisme_base"]))
        self.maintien_label.setText(str(resultats["calories_maintien"]))

        # Mettre à jour l'objectif calorique selon le mode
        if self.mode_auto_radio.isChecked():
            self.objectif_label.setText(str(resultats["calories_finales"]))

        # Mettre à jour le label de variation
        objectif = self.objectif_combo.currentText()
        taux = self.variation_spin.value()  # En grammes par semaine

        if objectif == "Perte de poids":
            # Utiliser la même formule que db_utilisateur.py
            # 1kg de graisse = 7700 kcal, donc 1g = 7.7 kcal
            deficit = round((taux * 7.7) / 7)  # Déficit journalier
            self.variation_label.setText(f"≈ -{deficit} kcal/jour")
        elif objectif == "Prise de masse":
            # Même formule pour le surplus
            surplus = round((taux * 7.7) / 7)  # Surplus journalier
            self.variation_label.setText(f"≈ +{surplus} kcal/jour")
        else:
            self.variation_label.setText("≈ 0 kcal/jour")

        # Calculer et mettre à jour les macros en grammes - après avoir défini l'objectif calorique
        macros = self.update_macro_grams()

        # En mode manuel, mettre à jour l'objectif avec les calories calculées par les macros
        if self.mode_manuel_radio.isChecked():
            self.objectif_label.setText(str(macros["total_kcal"]))

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

        # Taux en g/semaine
        variation = user_data.get("taux_variation", 0)
        self.variation_spin.setValue(variation)

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

        # Régime alimentaire
        regime = user_data.get("regime_alimentaire", "Régime équilibré")
        self.regime_combo.setCurrentText(regime)

        # Valeurs des macros en g/kg
        if regime == "Personnalisé":
            self.prot_min_spin.setValue(user_data.get("proteines_g_kg", 1.4))
            self.gluc_min_spin.setValue(user_data.get("glucides_g_kg", 3.0))
            self.lip_min_spin.setValue(user_data.get("lipides_g_kg", 0.9))

        # Activer/désactiver la modification selon le régime sélectionné
        is_custom = regime == "Personnalisé"
        self.prot_min_spin.setEnabled(is_custom)
        self.gluc_min_spin.setEnabled(is_custom)
        self.lip_min_spin.setEnabled(is_custom)

        # Calculer les calories
        self.calculer_calories()

    def sauvegarder_profil(self):
        """Sauvegarde le profil utilisateur dans la base de données"""
        # Récupérer les valeurs calculées des macros
        macros = self.update_macro_grams()

        # Récupérer l'objectif calorique (selon le mode)
        objectif_calories = int(self.objectif_label.text())

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
            "calories_personnalisees": (
                self.calories_manuelles_spin.value()
                if self.mode_manuel_radio.isChecked()
                else 0
            ),
            "regime_alimentaire": self.regime_combo.currentText(),
            "proteines_g_kg": self.prot_min_spin.value(),
            "glucides_g_kg": self.gluc_min_spin.value(),
            "lipides_g_kg": self.lip_min_spin.value(),
            "objectif_calories": objectif_calories,
            "objectif_proteines": macros["proteines_g"],
            "objectif_glucides": macros["glucides_g"],
            "objectif_lipides": macros["lipides_g"],
        }

        # Sauvegarder dans la base de données
        self.db_manager.sauvegarder_utilisateur(user_data)

        # Émettre le signal pour notifier de la modification du profil utilisateur
        EVENT_BUS.utilisateur_modifie.emit()

        # Afficher confirmation
        self.save_button.setText("Profil sauvegardé!")
        self.save_button.setObjectName("saveButtonPressed")

        # Forcer le rafraîchissement du style
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)

        # Réinitialiser le bouton après un délai de 2 secondes
        QTimer.singleShot(2000, self.reset_save_button)

    def reset_save_button(self):
        """Réinitialise l'apparence du bouton de sauvegarde"""
        self.save_button.setText("Sauvegarder le profil")
        self.save_button.setObjectName("saveButton")

        # Forcer le rafraîchissement du style
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)

    def refresh_data(self):
        """Implémentation de la méthode de base pour actualiser les données"""
        self.charger_donnees_utilisateur()
