from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal


class AlimentSliderWidget(QWidget):
    """Widget personnalisé pour ajuster la quantité d'un aliment avec un slider"""

    quantityChanged = Signal(int, float)  # aliment_id, new_quantity

    def __init__(self, aliment_id, aliment_nom, quantite_base, parent=None):
        super().__init__(parent)
        self.aliment_id = aliment_id
        self.aliment_nom = aliment_nom
        self.quantite_base = float(quantite_base)  # Conversion explicite en float
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Nom de l'aliment
        self.nom_label = QLabel(f"<b>{self.aliment_nom}</b>")
        layout.addWidget(self.nom_label)

        # Layout horizontal pour le slider et la quantité
        slider_layout = QHBoxLayout()

        # Quantité de base (référence visuelle)
        self.quantite_base_label = QLabel(f"{self.quantite_base:.0f}g")
        slider_layout.addWidget(self.quantite_base_label)

        # Slider pour ajuster la quantité (facteur de 0.1 à 3.0)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(10)  # 0.1x
        self.slider.setMaximum(300)  # 3.0x
        self.slider.setValue(100)  # 1.0x par défaut
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(50)  # Ticks tous les 0.5x
        self.slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.slider, 1)  # Stretch factor = 1

        # SpinBox pour la quantité directe en grammes - modification du pas à 1g au lieu de 5g
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(1)  # Minimum 1g
        self.spinbox.setMaximum(2000)  # Maximum 2000g
        self.spinbox.setSingleStep(1)  # Pas de 1g au lieu de 5g
        self.spinbox.setValue(int(self.quantite_base))
        self.spinbox.setSuffix("g")
        # Style pour rendre les boutons verticaux
        self.spinbox.setStyleSheet(
            """
            QSpinBox {
                padding-right: 5px;
                min-width: 80px;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 15px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 15px;
            }
        """
        )
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)
        slider_layout.addWidget(self.spinbox)

        layout.addLayout(slider_layout)

    def on_slider_changed(self, value):
        """Appelé quand le slider est déplacé"""
        # Convertir la valeur du slider en facteur (100 = 1.0x)
        facteur = value / 100.0

        # Calculer la nouvelle quantité en grammes
        nouvelle_quantite = self.quantite_base * facteur

        # Mettre à jour le spinbox avec la nouvelle quantité
        # Bloquer les signaux pour éviter une boucle de récursion
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(int(nouvelle_quantite))
        self.spinbox.blockSignals(False)

        # Émettre le signal avec l'ID de l'aliment et la nouvelle quantité
        self.quantityChanged.emit(self.aliment_id, nouvelle_quantite)

    def on_spinbox_changed(self, value):
        """Appelé quand la valeur du spinbox change"""
        # Convertir en float pour les calculs
        value_float = float(value)
        # Calculer le facteur à partir de la nouvelle quantité
        facteur = value_float / self.quantite_base

        # Mettre à jour le slider
        # Bloquer les signaux pour éviter une boucle de récursion
        self.slider.blockSignals(True)
        self.slider.setValue(int(facteur * 100))
        self.slider.blockSignals(False)

        # Émettre le signal avec l'ID de l'aliment et la nouvelle quantité
        self.quantityChanged.emit(self.aliment_id, value_float)

    def get_quantity(self):
        """Retourne la quantité actuelle"""
        return float(self.spinbox.value())

    def update_quantity_display(self, quantite):
        """Met à jour l'affichage de la quantité avec une valeur arrondie"""
        # Bloquer les signaux pour éviter les boucles
        self.spinbox.blockSignals(True)
        # Arrondir et mettre à jour la valeur
        self.spinbox.setValue(int(round(quantite)))
        self.spinbox.blockSignals(False)
