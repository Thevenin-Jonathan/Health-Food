from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """
    Bus d'événements centralisé pour la communication entre différents composants de l'application
    """

    semaine_ajoutee = Signal(
        int
    )  # Signal émis quand une semaine est ajoutée avec son ID
    semaine_supprimee = Signal(
        int
    )  # Signal émis quand une semaine est supprimée avec son ID
    semaines_modifiees = Signal()  # Signal général pour toute modification des semaines

    # Instance unique (singleton)
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance


# Créer l'instance unique accessible globalement
event_bus = EventBus.instance()
