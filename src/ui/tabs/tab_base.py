from PySide6.QtWidgets import QWidget


class TabBase(QWidget):
    """Classe de base pour tous les onglets de l'application"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

    def setup_ui(self):
        """Méthode à implémenter dans les classes dérivées pour configurer l'interface"""
        raise NotImplementedError(
            "Cette méthode doit être implémentée dans les classes dérivées"
        )

    def refresh_data(self):
        """Méthode à implémenter dans les classes dérivées pour actualiser les données"""
        pass
