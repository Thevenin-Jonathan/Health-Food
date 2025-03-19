from PySide6.QtWidgets import QDoubleSpinBox


def create_nutrition_spinbox(min_val, max_val, suffix, decimals):
    """
    Crée un spinbox formaté pour les valeurs nutritionnelles

    Args:
        min_val: Valeur minimale
        max_val: Valeur maximale
        suffix: Suffixe à afficher (ex: " kcal")
        decimals: Nombre de décimales

    Returns:
        QDoubleSpinBox: Le widget configuré
    """
    spinbox = QDoubleSpinBox()
    spinbox.setRange(min_val, max_val)
    spinbox.setSuffix(suffix)
    spinbox.setDecimals(decimals)
    spinbox.setMinimumWidth(100)
    spinbox.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
    spinbox.setStyleSheet(
        """
        QDoubleSpinBox {
            padding-right: 5px;
        }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
            width: 20px;
        }
    """
    )
    return spinbox
