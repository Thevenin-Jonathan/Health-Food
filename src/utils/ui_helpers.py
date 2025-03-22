from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
)
from PySide6.QtCore import QEvent, QObject, QTimer, Qt


class ButtonCursorHandler(QObject):
    """Gestionnaire d'événements pour les curseurs de boutons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.app.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Si c'est un événement d'entrée de souris sur un bouton
        if event.type() == QEvent.Enter and isinstance(obj, QPushButton):
            obj.setCursor(Qt.PointingHandCursor)

        # Si c'est un événement de sortie de souris sur un bouton
        elif event.type() == QEvent.Leave and isinstance(obj, QPushButton):
            obj.setCursor(Qt.ArrowCursor)

        return super().eventFilter(obj, event)


class LineEditSelectAllFilter(QObject):
    """Filtre d'événements qui sélectionne tout le texte au focus ou au clic"""

    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit):
            if event.type() == QEvent.FocusIn:
                QTimer.singleShot(0, obj.selectAll)
            elif event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
        return False


class AutoSelectTextEdit(QLineEdit):
    """QLineEdit qui sélectionne automatiquement tout son texte lors du focus"""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


class AutoSelectSpinBox(QSpinBox):
    """QSpinBox qui sélectionne automatiquement tout son texte lors du focus"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Installer le filtre sur le lineEdit
        self.lineEdit().installEventFilter(self)
        # Connecter le signal focusIn
        self.lineEdit().selectionChanged.connect(
            lambda: None
        )  # Empêcher la désélection

    def focusInEvent(self, event):
        """Sélectionne tout le texte quand le widget reçoit le focus"""
        super().focusInEvent(event)
        # Utiliser un timer pour sélectionner après l'événement standard
        QTimer.singleShot(0, self.lineEdit().selectAll)

    def eventFilter(self, obj, event):
        """Sélectionne tout le texte lors d'un clic"""
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
            elif event.type() == QEvent.FocusIn:
                QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


class AutoSelectDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox qui sélectionne automatiquement le texte lors du focus"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Installer le filtre sur le lineEdit
        self.lineEdit().installEventFilter(self)
        # Connecter le signal focusIn
        self.lineEdit().selectionChanged.connect(
            lambda: None
        )  # Empêcher la désélection

    def focusInEvent(self, event):
        """Sélectionne tout le texte quand le widget reçoit le focus"""
        super().focusInEvent(event)
        # Utiliser un timer pour sélectionner après l'événement standard
        QTimer.singleShot(0, self.lineEdit().selectAll)

    def eventFilter(self, obj, event):
        """Sélectionne tout le texte lors d'un clic"""
        if obj == self.lineEdit():
            if event.type() == QEvent.MouseButtonPress:
                QTimer.singleShot(0, obj.selectAll)
            elif event.type() == QEvent.FocusIn:
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
