from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QDialog,
)
from PySide6.QtCore import QEvent, QObject, QTimer, Qt


class ButtonCursorHandler(QObject):
    """Gestionnaire d'événements pour les curseurs de boutons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.app.installEventFilter(self)

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        # Si c'est un événement d'entrée de souris sur un bouton
        if event.type() == QEvent.Enter:
            # Gestion des boutons standards
            if isinstance(obj, QPushButton):
                obj.setCursor(Qt.PointingHandCursor)

            # Gestion des QLabel avec classe spécifique ou propriété "cursor-pointer"
            elif isinstance(obj, QLabel):
                # Vérifier si le label a la propriété "cursor-pointer" ou une classe spécifique
                if (
                    obj.property("cursor-pointer") is True
                    or obj.property("warning-icon") is True
                ):
                    obj.setCursor(Qt.PointingHandCursor)

        # Si c'est un événement de sortie de souris
        elif event.type() == QEvent.Leave:
            if isinstance(obj, QPushButton):
                obj.setCursor(Qt.ArrowCursor)
            elif isinstance(obj, QLabel):
                if (
                    obj.property("cursor-pointer") is True
                    or obj.property("warning-icon") is True
                ):
                    obj.setCursor(Qt.ArrowCursor)

        return super().eventFilter(obj, event)


class LineEditSelectAllFilter(QObject):
    """Filtre d'événements qui sélectionne tout le texte au clic souris uniquement"""

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        if isinstance(obj, QLineEdit):
            # Sélectionner uniquement au clic de souris, pas au focus clavier
            if event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
        return False


class AutoSelectTextEdit(QLineEdit):
    """QLineEdit qui sélectionne automatiquement tout son texte lors du clic souris"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        if obj == self and event.type() == QEvent.MouseButtonPress:
            QTimer.singleShot(0, self.selectAll)
        return super().eventFilter(obj, event)


class AutoSelectSpinBox(QSpinBox):
    """QSpinBox qui sélectionne automatiquement tout son texte lors du clic souris"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Installer le filtre sur le lineEdit
        self.lineEdit().installEventFilter(self)
        # Connecter le signal focusIn
        self.lineEdit().selectionChanged.connect(
            lambda: None
        )  # Empêcher la désélection

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        """Sélectionne tout le texte lors d'un clic (pas de sélection au focus)"""
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


class AutoSelectDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox qui sélectionne automatiquement le texte lors du clic souris"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Installer le filtre sur le lineEdit
        self.lineEdit().installEventFilter(self)
        # Connecter le signal focusIn
        self.lineEdit().selectionChanged.connect(
            lambda: None
        )  # Empêcher la désélection

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        """Sélectionne tout le texte lors d'un clic (pas de sélection au focus)"""
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


def apply_auto_select_to_widget(widget):
    """
    Parcourt récursivement tous les widgets enfants et applique
    la fonctionnalité de sélection automatique aux champs de saisie
    """
    for child in widget.findChildren(QLineEdit):
        child.installEventFilter(LineEditSelectAllFilter(child))

    for child in widget.findChildren(QSpinBox):
        child.lineEdit().installEventFilter(LineEditSelectAllFilter(child.lineEdit()))

    for child in widget.findChildren(QDoubleSpinBox):
        child.lineEdit().installEventFilter(LineEditSelectAllFilter(child.lineEdit()))


# Classe pour intercepter les dialogues et appliquer l'auto-select
class DialogAutoSelectFilter(QObject):
    """Filtre d'événements qui applique la sélection automatique à tous les dialogues"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.app.installEventFilter(self)

    def eventFilter(self, obj, event):  # pylint: disable=invalid-name
        # Lorsqu'un widget reçoit un événement Show et que c'est un QDialog
        if event.type() == QEvent.Show and isinstance(obj, QDialog):
            # Utiliser QTimer pour s'assurer que le dialogue est complètement initialisé
            QTimer.singleShot(10, lambda: apply_auto_select_to_widget(obj))
        return super().eventFilter(obj, event)
