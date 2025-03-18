from .db_connector import DBConnector
from .db_utilisateur import UserManager
from .db_aliments import AlimentsManager
from .db_repas import RepasManager
from .db_repas_types import RepasTypesManager


class DatabaseManager(DBConnector):
    """
    Gestionnaire principal de base de données qui délègue aux gestionnaires spécialisés.
    Cette classe coordonne les différents gestionnaires pour fournir une interface unifiée.
    """

    def __init__(self, db_file="nutrition_sportive.db"):
        """Initialise le gestionnaire de base de données global"""
        super().__init__(db_file)

        # Initialisation des gestionnaires spécialisés
        self.user_manager = UserManager(db_file)
        self.aliment_manager = AlimentsManager(db_file)
        self.repas_manager = RepasManager(db_file)
        self.repas_types_manager = RepasTypesManager(db_file)

    # =========== MÉTHODES DÉLÉGUÉES À UserManager ===========
    def sauvegarder_utilisateur(self, data):
        """Délègue la sauvegarde des données utilisateur au UserManager"""
        return self.user_manager.sauvegarder_utilisateur(data)

    def get_utilisateur(self):
        """Délègue la récupération des données utilisateur au UserManager"""
        return self.user_manager.get_utilisateur()

    def calculer_calories_journalieres(self, user_data=None):
        """Délègue le calcul des besoins caloriques au UserManager"""
        return self.user_manager.calculer_calories_journalieres(user_data)

    # =========== MÉTHODES DÉLÉGUÉES À AlimentManager ===========
    def ajouter_aliment(self, data):
        """Délègue l'ajout d'aliment à l'AlimentManager"""
        return self.aliment_manager.ajouter_aliment(data)

    def get_aliments(self, categorie=None, recherche=None):
        """Délègue la récupération des aliments à l'AlimentManager"""
        return self.aliment_manager.get_aliments(categorie, recherche)

    def get_aliment(self, aliment_id):
        """Délègue la récupération d'un aliment à l'AlimentManager"""
        return self.aliment_manager.get_aliment(aliment_id)

    def supprimer_aliment(self, aliment_id):
        """Délègue la suppression d'un aliment à l'AlimentManager"""
        return self.aliment_manager.supprimer_aliment(aliment_id)

    # =========== MÉTHODES DÉLÉGUÉES À RepasManager ===========
    def ajouter_repas(self, nom, jour, ordre, semaine_id=None):
        """Délègue l'ajout de repas au RepasManager"""
        return self.repas_manager.ajouter_repas(nom, jour, ordre, semaine_id)

    def ajouter_aliment_repas(self, repas_id, aliment_id, quantite):
        """Délègue l'ajout d'aliment à un repas au RepasManager"""
        return self.repas_manager.ajouter_aliment_repas(repas_id, aliment_id, quantite)

    def supprimer_aliment_repas(self, repas_id, aliment_id):
        """Délègue la suppression d'un aliment d'un repas au RepasManager"""
        return self.repas_manager.supprimer_aliment_repas(repas_id, aliment_id)

    def get_repas(self, repas_id):
        """Délègue la récupération d'un repas au RepasManager"""
        return self.repas_manager.get_repas(repas_id)

    def get_repas_semaine(self, semaine_id=None):
        """Délègue la récupération des repas d'une semaine au RepasManager"""
        return self.repas_manager.get_repas_semaine(semaine_id)

    def get_semaines_existantes(self):
        """Récupère tous les IDs de semaines qui existent dans la base de données"""
        return self.repas_manager.get_semaines_existantes()  # Déléguer à RepasManager

    def generer_liste_courses(self, semaine_id=None):
        """Délègue la génération de la liste de courses au RepasManager"""
        return self.repas_manager.generer_liste_courses(semaine_id)

    def supprimer_repas(self, repas_id):
        """Délègue la suppression d'un repas au RepasManager"""
        return self.repas_manager.supprimer_repas(repas_id)

    def supprimer_semaine(self, semaine_id):
        """Délègue la suppression d'une semaine au RepasManager"""
        return self.repas_manager.supprimer_semaine(semaine_id)

    # =========== MÉTHODES DÉLÉGUÉES À RepasTypesManager ===========
    def ajouter_repas_type(self, nom, description):
        """Délègue l'ajout d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.ajouter_repas_type(nom, description)

    def ajouter_aliment_repas_type(self, repas_type_id, aliment_id, quantite):
        """Délègue l'ajout d'aliment à un repas type au RepasTypesManager"""
        return self.repas_types_manager.ajouter_aliment_repas_type(
            repas_type_id, aliment_id, quantite
        )

    def supprimer_aliment_repas_type(self, repas_type_id, aliment_id):
        """Délègue la suppression d'un aliment d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.supprimer_aliment_repas_type(
            repas_type_id, aliment_id
        )

    def get_repas_types(self):
        """Délègue la récupération de tous les repas types au RepasTypesManager"""
        return self.repas_types_manager.get_repas_types()

    def get_repas_type(self, id):
        """Délègue la récupération d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.get_repas_type(id)

    def supprimer_repas_type(self, id):
        """Délègue la suppression d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.supprimer_repas_type(id)

    def appliquer_repas_type_au_jour(self, repas_type_id, jour, ordre, semaine_id=None):
        """Délègue l'application d'un repas type à un jour au RepasTypesManager"""
        return self.repas_types_manager.appliquer_repas_type_au_jour(
            repas_type_id, jour, ordre, semaine_id
        )
