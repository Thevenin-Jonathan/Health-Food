from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QSizePolicy,
    QSpacerItem,
    QApplication,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class UpdateDialog(QDialog):
    """Boîte de dialogue pour afficher et gérer les mises à jour"""

    update_requested = Signal()
    download_requested = Signal()

    def __init__(self, update_info, parent=None):
        super().__init__(parent)

        self.update_info = update_info
        self.setWindowTitle("Mise à jour disponible")
        self.setMinimumWidth(500)

        # Configuration du layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # En-tête de la mise à jour
        header_layout = QHBoxLayout()

        # Icône de mise à jour (optionnel - ajoutez votre propre icône)
        header_layout.addWidget(QLabel("🔄"))

        # Titre de la mise à jour
        title = QLabel("Une nouvelle version est disponible !")
        title.setFont(QFont(title.font().family(), 14, QFont.Bold))
        title.setStyleSheet("color: #2E7D32;")  # Vert foncé
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Information de version
        version_layout = QHBoxLayout()
        version_layout.addWidget(
            QLabel(f"Version actuelle: v{update_info.get('current_version', '?')}")
        )
        version_layout.addStretch()

        new_version = QLabel(f"Nouvelle version: v{update_info.get('version', '?')}")
        new_version.setStyleSheet("font-weight: bold; color: #2E7D32;")
        version_layout.addWidget(new_version)

        # Notes de mise à jour
        notes_label = QLabel("Notes de mise à jour:")
        notes_label.setFont(QFont(notes_label.font().family(), weight=QFont.Bold))

        notes_text = QTextEdit()
        notes_text.setReadOnly(True)
        notes_text.setPlainText(
            update_info.get("release_notes", "Pas de notes disponibles")
        )
        notes_text.setMinimumHeight(120)

        # Barre de progression (cachée initialement)
        self.progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Téléchargement en cours...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar)

        # Boutons
        buttons_layout = QHBoxLayout()

        self.remind_button = QPushButton("Me le rappeler plus tard")
        self.remind_button.clicked.connect(self.reject)

        self.download_button = QPushButton("Télécharger maintenant")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self._on_download_clicked)

        # État initial des boutons
        self.is_downloading = False

        buttons_layout.addWidget(self.remind_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.download_button)

        # Ajouter tous les widgets au layout principal
        layout.addLayout(header_layout)
        layout.addLayout(version_layout)
        layout.addWidget(notes_label)
        layout.addWidget(notes_text)
        layout.addLayout(self.progress_layout)
        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        layout.addLayout(buttons_layout)

        # Cacher la barre de progression au départ
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

    def set_progress(self, value):
        """Mettre à jour la barre de progression"""
        if not self.progress_bar.isVisible():
            self.progress_label.setVisible(True)
            self.progress_bar.setVisible(True)

        self.progress_bar.setValue(value)
        QApplication.processEvents()  # Assurer que l'UI est mise à jour

    def set_downloading(self, is_downloading):
        """Changer l'état du téléchargement"""
        self.is_downloading = is_downloading

        if is_downloading:
            self.download_button.setText("Installation en cours...")
            self.download_button.setEnabled(False)
            self.remind_button.setEnabled(False)
        else:
            self.download_button.setText("Télécharger maintenant")
            self.download_button.setEnabled(True)
            self.remind_button.setEnabled(True)

    def _on_download_clicked(self):
        """Gérer le clic sur le bouton de téléchargement"""
        if not self.is_downloading:
            self.download_requested.emit()
            self.set_downloading(True)


class UpdateReadyDialog(QDialog):
    """Boîte de dialogue indiquant que la mise à jour est prête à être installée"""

    install_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Mise à jour prête")
        self.setMinimumWidth(400)

        # Configuration du layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Message
        message = QLabel(
            "La mise à jour a été téléchargée avec succès et est prête à être installée.\n\n"
            "L'application va se fermer pour procéder à l'installation."
        )
        message.setWordWrap(True)

        # Boutons
        buttons_layout = QHBoxLayout()

        later_button = QPushButton("Installer plus tard")
        later_button.clicked.connect(self.reject)

        install_button = QPushButton("Installer maintenant")
        install_button.setObjectName("primaryButton")
        install_button.clicked.connect(self._on_install_clicked)

        buttons_layout.addWidget(later_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(install_button)

        # Ajouter les widgets au layout
        layout.addWidget(message)
        layout.addSpacerItem(
            QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        layout.addLayout(buttons_layout)

    def _on_install_clicked(self):
        """Gérer le clic sur le bouton d'installation"""
        self.install_requested.emit()
        self.accept()
