from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QFormLayout,
    QMessageBox,
    QCompleter,
)
from PySide6.QtCore import Qt


class AjouterAlimentDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()
        self.charger_suggestions()

    def setup_ui(self):
        self.setWindowTitle("Ajouter un aliment")
        self.setMinimumWidth(400)

        layout = QFormLayout()

        # Nom de l'aliment
        self.nom_input = QLineEdit()
        layout.addRow("Nom:", self.nom_input)

        # Marque avec auto-complétion
        self.marque_input = QComboBox()
        self.marque_input.setEditable(True)
        self.marque_input.setCurrentText("")
        layout.addRow("Marque:", self.marque_input)

        # Boutons rapides pour les marques récentes directement sous le champ marque
        self.marques_recentes_layout = QHBoxLayout()
        layout.addRow("", self.marques_recentes_layout)

        # Magasin avec auto-complétion
        self.magasin_input = QComboBox()
        self.magasin_input.setEditable(True)
        self.magasin_input.setCurrentText("")
        layout.addRow("Magasin:", self.magasin_input)

        # Boutons rapides pour les magasins récents directement sous le champ magasin
        self.magasins_recents_layout = QHBoxLayout()
        layout.addRow("", self.magasins_recents_layout)

        # Catégorie
        self.categorie_input = QLineEdit()
        layout.addRow("Catégorie:", self.categorie_input)

        # Valeurs nutritionnelles
        self.calories_input = QDoubleSpinBox()
        self.calories_input.setMinimum(0)
        self.calories_input.setMaximum(1000)
        self.calories_input.setValue(0)
        self.calories_input.setSuffix(" kcal")
        layout.addRow("Calories:", self.calories_input)

        self.proteines_input = QDoubleSpinBox()
        self.proteines_input.setMinimum(0)
        self.proteines_input.setMaximum(100)
        self.proteines_input.setValue(0)
        self.proteines_input.setSuffix(" g")
        layout.addRow("Protéines:", self.proteines_input)

        self.glucides_input = QDoubleSpinBox()
        self.glucides_input.setMinimum(0)
        self.glucides_input.setMaximum(100)
        self.glucides_input.setValue(0)
        self.glucides_input.setSuffix(" g")
        layout.addRow("Glucides:", self.glucides_input)

        self.lipides_input = QDoubleSpinBox()
        self.lipides_input.setMinimum(0)
        self.lipides_input.setMaximum(100)
        self.lipides_input.setValue(0)
        self.lipides_input.setSuffix(" g")
        layout.addRow("Lipides:", self.lipides_input)

        self.fibres_input = QDoubleSpinBox()
        self.fibres_input.setMinimum(0)
        self.fibres_input.setMaximum(100)
        self.fibres_input.setValue(0)
        self.fibres_input.setSuffix(" g")
        layout.addRow("Fibres:", self.fibres_input)

        self.prix_input = QDoubleSpinBox()
        self.prix_input.setMinimum(0)
        self.prix_input.setMaximum(1000)
        self.prix_input.setValue(0)
        self.prix_input.setSuffix(" €/kg")
        layout.addRow("Prix au kilo:", self.prix_input)

        # Boutons
        buttons_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Ajouter")
        self.btn_save.clicked.connect(self.accept)

        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)

        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def charger_suggestions(self):
        """Charge les suggestions de marques et magasins basées sur les aliments existants"""
        if not self.db_manager:
            print("Erreur: gestionnaire de base de données non disponible")
            return

        try:
            # Récupérer toutes les marques et magasins uniques de la base de données
            marques = self.db_manager.get_marques_uniques()
            magasins = self.db_manager.get_magasins_uniques()

            # Configurer l'autocomplétion pour les ComboBox
            self.marque_input.clear()
            self.magasin_input.clear()

            # Ajouter les éléments pour l'autocomplétion
            if marques:
                self.marque_input.addItems(marques)
                self.marque_input.setCurrentText("")

                # Activer l'autocomplétion
                completer = QCompleter(marques)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.marque_input.setCompleter(completer)

            if magasins:
                self.magasin_input.addItems(magasins)
                self.magasin_input.setCurrentText("")

                # Activer l'autocomplétion
                completer = QCompleter(magasins)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                self.magasin_input.setCompleter(completer)

            # Ajouter des boutons rapides pour les marques/magasins les plus fréquents
            if marques:
                self.ajouter_boutons_rapides(
                    marques[:5], self.marques_recentes_layout, self.marque_input
                )
            if magasins:
                self.ajouter_boutons_rapides(
                    magasins[:5], self.magasins_recents_layout, self.magasin_input
                )
        except Exception as e:
            print(f"Erreur lors du chargement des suggestions: {e}")
            import traceback

            traceback.print_exc()

    def ajouter_boutons_rapides(self, items, layout, target_input):
        """Ajoute des boutons rapides pour sélectionner les items les plus fréquents"""
        # Nettoyer le layout existant
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Ajouter des boutons pour chaque item
        for item in items:
            if item:  # S'assurer que l'item n'est pas vide
                btn = QPushButton(item)
                btn.setFixedHeight(25)  # Hauteur fixe pour améliorer l'apparence
                # Style amélioré avec des couleurs contrastées et lisibles
                btn.setStyleSheet(
                    """
                  QPushButton {
                    background-color: #ccffcc;  # Vert clair
                    color: #333333;
                    border: 1px solid #99cc99;
                    border-radius: 3px;
                    padding: 2px 8px;
                    font-size: 11px;
                  }
                  QPushButton:hover {
                    background-color: #b3ffb3;  # Vert encore plus clair au survol
                    border-color: #66b266;
                  }
                """
                )
                btn.clicked.connect(
                    lambda checked=False, text=item: target_input.setCurrentText(text)
                )
                layout.addWidget(btn)

        # Ajouter un espaceur pour aligner à gauche
        layout.addStretch()

    def get_data(self):
        """Récupère les données saisies dans le formulaire"""
        return {
            "nom": self.nom_input.text().strip(),
            "marque": self.marque_input.currentText().strip(),
            "magasin": self.magasin_input.currentText().strip(),
            "categorie": self.categorie_input.text().strip(),
            "calories": self.calories_input.value(),
            "proteines": self.proteines_input.value(),
            "glucides": self.glucides_input.value(),
            "lipides": self.lipides_input.value(),
            "fibres": self.fibres_input.value(),
            "prix_kg": self.prix_input.value(),
        }
