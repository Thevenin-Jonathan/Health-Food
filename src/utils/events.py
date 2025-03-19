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

    # Nouveaux signaux pour les aliments
    aliment_supprime = Signal(int)  # Signal émis quand un aliment est supprimé (ID)
    aliment_modifie = Signal(int)  # Signal émis quand un aliment est modifié (ID)
    aliment_ajoute = Signal(int)  # Signal émis quand un aliment est ajouté (ID)
    aliments_modifies = Signal()  # Signal général pour toute modification des aliments

    # Nouveaux signaux pour les repas
    repas_ajoute = Signal(int)  # Signal émis quand un repas est ajouté (ID)
    repas_supprime = Signal(int)  # Signal émis quand un repas est supprimé (ID)
    repas_modifies = Signal(
        int
    )  # Signal émis quand des repas sont modifiés (semaine_id)

    utilisateur_modifie = (
        Signal()
    )  # Signal émis quand le profil utilisateur est modifié

    # Instance unique (singleton)
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance


# Créer l'instance unique accessible globalement
EVENT_BUS = EventBus.instance()
