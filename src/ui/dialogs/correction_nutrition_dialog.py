from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
)


class CorrectionNutritionDialog(QDialog):
    """Dialogue pour corriger les valeurs nutritionnelles d'un aliment"""

    def __init__(self, parent, aliment, db_manager):
        super().__init__(parent)
        self.aliment = aliment
        self.db_manager = db_manager
        self.setWindowTitle(f"Corriger les valeurs nutritionnelles - {aliment['nom']}")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Explications
        info_label = QLabel(
            "Les valeurs nutritionnelles de cet aliment semblent incohérentes. "
            "Vous pouvez les corriger ci-dessous :"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Formulaire pour les valeurs
        form_layout = QFormLayout()

        self.calories_input = QDoubleSpinBox()
        self.calories_input.setRange(0, 1000)
        self.calories_input.setValue(self.aliment["calories"])
        self.calories_input.setSuffix(" kcal")
        self.calories_input.setProperty("class", "spin-box-vertical")
        form_layout.addRow("Calories (pour 100g):", self.calories_input)

        self.proteines_input = QDoubleSpinBox()
        self.proteines_input.setRange(0, 100)
        self.proteines_input.setValue(self.aliment["proteines"])
        self.proteines_input.setSuffix(" g")
        self.proteines_input.setProperty("class", "spin-box-vertical")
        form_layout.addRow("Protéines (pour 100g):", self.proteines_input)

        self.glucides_input = QDoubleSpinBox()
        self.glucides_input.setRange(0, 100)
        self.glucides_input.setValue(self.aliment["glucides"])
        self.glucides_input.setSuffix(" g")
        self.glucides_input.setProperty("class", "spin-box-vertical")
        form_layout.addRow("Glucides (pour 100g):", self.glucides_input)

        self.lipides_input = QDoubleSpinBox()
        self.lipides_input.setRange(0, 100)
        self.lipides_input.setValue(self.aliment["lipides"])
        self.lipides_input.setSuffix(" g")
        self.lipides_input.setProperty("class", "spin-box-vertical")
        form_layout.addRow("Lipides (pour 100g):", self.lipides_input)

        layout.addLayout(form_layout)

        # Afficher les calories calculées
        self.calories_calculated_label = QLabel()
        self.update_calculated_calories()
        self.proteines_input.valueChanged.connect(self.update_calculated_calories)
        self.glucides_input.valueChanged.connect(self.update_calculated_calories)
        self.lipides_input.valueChanged.connect(self.update_calculated_calories)
        layout.addWidget(self.calories_calculated_label)

        # Option pour recalculer automatiquement les calories
        self.recalculate_btn = QPushButton(
            "Recalculer les calories à partir des macros"
        )
        self.recalculate_btn.clicked.connect(self.recalculate_calories)
        layout.addWidget(self.recalculate_btn)

        # Boutons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def update_calculated_calories(self):
        """Met à jour l'affichage des calories calculées"""
        proteines = self.proteines_input.value()
        glucides = self.glucides_input.value()
        lipides = self.lipides_input.value()

        calories_calculees = (proteines * 4) + (glucides * 4) + (lipides * 9)

        # Calculer l'écart avec les calories indiquées
        calories_indiquees = self.calories_input.value()
        if calories_calculees > 0:
            ecart_pct = (
                abs(calories_indiquees - calories_calculees) / calories_calculees * 100
            )
            ecart_txt = f"{ecart_pct:.1f}%"
        else:
            ecart_txt = "N/A"

        self.calories_calculated_label.setText(
            f"<b>Calories calculées à partir des macros: {calories_calculees:.1f} kcal</b><br>"
            f"Écart avec les calories indiquées: {ecart_txt}"
        )

    def recalculate_calories(self):
        """Recalcule automatiquement les calories à partir des macros"""
        proteines = self.proteines_input.value()
        glucides = self.glucides_input.value()
        lipides = self.lipides_input.value()

        calories_calculees = (proteines * 4) + (glucides * 4) + (lipides * 9)
        self.calories_input.setValue(calories_calculees)
        self.update_calculated_calories()

    def get_updated_values(self):
        """Retourne les valeurs mises à jour"""
        return {
            "calories": self.calories_input.value(),
            "proteines": self.proteines_input.value(),
            "glucides": self.glucides_input.value(),
            "lipides": self.lipides_input.value(),
        }
