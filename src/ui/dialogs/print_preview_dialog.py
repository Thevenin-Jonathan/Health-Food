from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
)


class PrintPreviewDialog(QDialog):
    """Dialogue d'aperçu avant impression"""

    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aperçu avant impression")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Aperçu du contenu
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setHtml(content)
        layout.addWidget(self.preview)

        # Boutons
        btn_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_print = QPushButton("Imprimer")
        self.btn_print.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_print)
        layout.addLayout(btn_layout)
