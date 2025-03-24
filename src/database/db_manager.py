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
        self.user_manager = UserManager(self.db_file)
        self.aliment_manager = AlimentsManager(self.db_file)
        self.repas_manager = RepasManager(self.db_file)
        self.repas_types_manager = RepasTypesManager(self.db_file)

    def init_db(self):
        """Initialise la structure de la base de données et crée un utilisateur par défaut si nécessaire"""
        # Créer les tables de la base de données
        super().init_db()

        # Une fois les tables créées, vérifier si un utilisateur existe déjà
        self.connect()
        try:
            user_count = self.cursor.execute(
                "SELECT COUNT(*) FROM utilisateur"
            ).fetchone()[0]
            if user_count == 0:
                # Aucun utilisateur trouvé, créer un profil par défaut
                print("Aucun utilisateur trouvé, création d'un profil par défaut...")
                default_user_data = {
                    "nom": "Utilisateur",
                    "sexe": "Homme",
                    "age": 30,
                    "taille": 175,
                    "poids": 75,
                    "niveau_activite": "Modéré",
                    "objectif": "Maintien",
                    "taux_variation": 0,
                    "calories_personnalisees": 0,
                    "regime_alimentaire": "Régime équilibré",
                    "proteines_g_kg": 1.8,
                    "glucides_g_kg": 3.0,
                    "lipides_g_kg": 1.0,
                    "objectif_calories": 2500,
                    "objectif_proteines": 125,
                    "objectif_glucides": 300,
                    "objectif_lipides": 83,
                    "theme_actif": "Vert Nature",
                }
                self.sauvegarder_utilisateur(default_user_data)
        except Exception as e:
            print(
                f"Erreur lors de la vérification/création de l'utilisateur par défaut: {e}"
            )
        finally:
            self.disconnect()

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

    def save_user_theme(self, theme_name):
        """Délègue la sauvegarde du thème utilisateur"""
        return self.user_manager.save_user_theme(theme_name)

    def get_user_theme(self):
        """Délègue la récupération du thème utilisateur"""
        return self.user_manager.get_user_theme()

    # =========== MÉTHODES DÉLÉGUÉES À AlimentManager ===========
    def ajouter_aliment(self, data):
        """Délègue l'ajout d'aliment à l'AlimentManager"""
        return self.aliment_manager.ajouter_aliment(data)

    def modifier_aliment(self, aliment_id, data):
        """Délègue la modification d'un aliment à l'AlimentManager"""
        return self.aliment_manager.modifier_aliment(aliment_id, data)

    def get_aliments(
        self,
        categorie=None,
        marque=None,
        magasin=None,
        recherche=None,
        sort_column=None,
        sort_order=None,
    ):
        """Délègue la récupération des aliments avec options de tri"""
        return self.aliment_manager.get_aliments(
            categorie=categorie,
            marque=marque,
            magasin=magasin,
            recherche=recherche,
            sort_column=sort_column,
            sort_order=sort_order,
        )

    def get_aliment(self, aliment_id):
        """Délègue la récupération d'un aliment à l'AlimentManager"""
        return self.aliment_manager.get_aliment(aliment_id)

    def supprimer_aliment(self, aliment_id):
        """Délègue la suppression d'un aliment à l'AlimentManager"""
        return self.aliment_manager.supprimer_aliment(aliment_id)

    def get_marques_uniques(self):
        """Délègue la récupération des marques uniques à l'AlimentManager"""
        return self.aliment_manager.get_marques_uniques()

    def get_magasins_uniques(self):
        """Délègue la récupération des magasins uniques à l'AlimentManager"""
        return self.aliment_manager.get_magasins_uniques()

    def get_categories_uniques(self):
        """Délègue la récupération des catégories uniques à l'AlimentManager"""
        return self.aliment_manager.get_categories_uniques()

    # =========== MÉTHODES DÉLÉGUÉES À RepasManager ===========
    def ajouter_repas(self, nom, jour, ordre, semaine_id=None, repas_type_id=None):
        """Délègue l'ajout de repas au RepasManager"""
        return self.repas_manager.ajouter_repas(
            nom, jour, ordre, semaine_id, repas_type_id
        )

    def ajouter_aliment_repas(self, repas_id, aliment_id, quantite):
        """Délègue l'ajout d'aliment à un repas au RepasManager"""
        return self.repas_manager.ajouter_aliment_repas(repas_id, aliment_id, quantite)

    def supprimer_aliment_repas(self, repas_id, aliment_id):
        """Délègue la suppression d'un aliment d'un repas au RepasManager"""
        return self.repas_manager.supprimer_aliment_repas(repas_id, aliment_id)

    def get_aliments_repas(self, repas_id):
        """Délègue la récupération des aliments d'un repas au RepasManager"""
        return self.repas_manager.get_aliments_repas(repas_id)

    def get_repas_semaine(self, semaine_id=None):
        """Délègue la récupération des repas d'une semaine au RepasManager"""
        return self.repas_manager.get_repas_semaine(semaine_id)

    def decaler_ordres(self, jour, semaine_id, ordre_insertion):
        """Délègue le décalage des ordres au RepasManager"""
        return self.repas_manager.decaler_ordres(jour, semaine_id, ordre_insertion)

    def normaliser_ordres(self, jour, semaine_id):
        """Réindexe les ordres pour qu'ils soient des entiers consécutifs (1, 2, 3...)"""
        return self.repas_manager.normaliser_ordres(jour, semaine_id)

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

    def changer_jour_repas(self, repas_id, nouveau_jour, nouvel_ordre):
        """Délègue le changement de jour d'un repas au RepasManager"""
        return self.repas_manager.changer_jour_repas(
            repas_id, nouveau_jour, nouvel_ordre
        )

    def modifier_nom_repas(self, repas_id, nouveau_nom):
        """Délègue la modification du nom d'un repas au RepasManager"""
        return self.repas_manager.modifier_nom_repas(repas_id, nouveau_nom)

    def update_repas_based_on_recipe(self, repas_type_id):
        """Délègue la mise à jour des repas basés sur une recette au RepasManager"""
        return self.repas_manager.update_repas_based_on_recipe(repas_type_id)

    def get_repas(self, repas_id):
        """Délègue la récupération d'un repas par son ID au RepasManager"""
        return self.repas_manager.get_repas(repas_id)

    def modifier_quantite_aliment_repas(self, repas_id, aliment_id, quantite):
        """Délègue la modification de la quantité d'un aliment dans un repas au RepasManager"""
        return self.repas_manager.modifier_quantite_aliment_repas(
            repas_id, aliment_id, quantite
        )

    def sauvegarder_nom_semaine(self, semaine_id, nom_personnalise):
        """Délègue la sauvegarde du nom personnalisé d'une semaine au RepasManager"""
        return self.repas_manager.sauvegarder_nom_semaine(semaine_id, nom_personnalise)

    def get_noms_semaines(self):
        """Délègue la récupération des noms personnalisés des semaines au RepasManager"""
        return self.repas_manager.get_noms_semaines()

    def supprimer_nom_semaine(self, semaine_id):
        """Délègue la suppression du nom personnalisé d'une semaine au RepasManager"""
        return self.repas_manager.supprimer_nom_semaine(semaine_id)

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

    def get_repas_type(self, repas_id):
        """Délègue la récupération d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.get_repas_type(repas_id)

    def supprimer_repas_type(self, repas_type_id):
        """Délègue la suppression d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.supprimer_repas_type(repas_type_id)

    def appliquer_repas_type_au_jour(
        self, repas_type_id, jour, ordre, semaine_id=None, nom_personnalise=None
    ):
        """Délègue l'application d'un repas type à un jour au RepasTypesManager"""
        return self.repas_types_manager.appliquer_repas_type_au_jour(
            repas_type_id, jour, ordre, semaine_id, nom_personnalise
        )

    def modifier_quantite_aliment_repas_type(self, repas_type_id, aliment_id, quantite):
        """Délègue la modification de la quantité d'un aliment dans un repas type"""
        return self.repas_types_manager.modifier_quantite_aliment_repas_type(
            repas_type_id, aliment_id, quantite
        )

    def modifier_repas_type(self, repas_type_id, nom, description):
        """Délègue la modification d'un repas type au RepasTypesManager"""
        return self.repas_types_manager.modifier_repas_type(
            repas_type_id, nom, description
        )

    def appliquer_repas_type_au_jour_avec_facteurs(
        self, repas_type_id, jour, ordre, semaine_id=None, facteurs_quantite=None
    ):
        """Délègue l'application d'un repas type à un jour avec des facteurs d'ajustement"""
        return self.repas_types_manager.appliquer_repas_type_au_jour_avec_facteurs(
            repas_type_id, jour, ordre, semaine_id, facteurs_quantite
        )

    def appliquer_recette_modifiee_au_jour(
        self, recette_base_id, liste_ingredients, jour, ordre, semaine_id=None
    ):
        """Délègue l'application d'une recette modifiée à un jour"""
        return self.repas_types_manager.appliquer_recette_modifiee_au_jour(
            recette_base_id, liste_ingredients, jour, ordre, semaine_id
        )

    # =========== MÉTHODES D'EXPORTATION ET D'IMPORTATION ===========
    def exporter_aliments(self):
        """Exporte tous les aliments de la base de données"""
        self.connect()
        self.cursor.execute("SELECT * FROM aliments")
        aliments = [dict(row) for row in self.cursor.fetchall()]
        self.disconnect()
        return aliments

    def exporter_repas_types(self):
        """Exporte tous les repas types avec leurs aliments"""
        return self.repas_types_manager.get_repas_types()

    def exporter_planning(self, semaine_id=None):
        """Exporte les repas d'une semaine spécifique ou de la semaine courante"""
        return self.repas_manager.get_repas_semaine(semaine_id)

    def importer_aliments(self, aliments_data):
        """Importe des aliments depuis un dictionnaire"""
        count = 0
        for aliment in aliments_data:
            # Vérifier si l'aliment existe déjà par nom et marque
            self.connect()
            self.cursor.execute(
                "SELECT id FROM aliments WHERE nom = ? AND marque = ?",
                (aliment["nom"], aliment["marque"]),
            )
            existing = self.cursor.fetchone()
            self.disconnect()

            if existing:
                # Mise à jour de l'aliment existant
                aliment_id = existing[0]
                self.modifier_aliment(aliment_id, aliment)
            else:
                # Ajout d'un nouvel aliment
                self.ajouter_aliment(aliment)
            count += 1
        return count

    def importer_repas_types(self, repas_types_data):
        """Importe des repas types depuis un dictionnaire"""
        count = 0
        for repas_type in repas_types_data:
            # Vérifier si le repas type existe déjà
            self.connect()
            self.cursor.execute(
                "SELECT id FROM repas_types WHERE nom = ?", (repas_type["nom"],)
            )
            existing = self.cursor.fetchone()
            self.disconnect()

            aliments = repas_type.pop("aliments", [])

            if existing:
                # Mise à jour du repas type existant
                repas_type_id = existing[0]
                self.modifier_repas_type(
                    repas_type_id, repas_type["nom"], repas_type.get("description", "")
                )

                # Supprimer les aliments existants
                for aliment in self.repas_types_manager.get_repas_type(repas_type_id)[
                    "aliments"
                ]:
                    self.supprimer_aliment_repas_type(repas_type_id, aliment["id"])
            else:
                # Ajout d'un nouveau repas type
                repas_type_id = self.ajouter_repas_type(
                    repas_type["nom"], repas_type.get("description", "")
                )

            # Ajouter les aliments au repas type
            for aliment in aliments:
                # Chercher l'ID de l'aliment par nom
                self.connect()
                self.cursor.execute(
                    "SELECT id FROM aliments WHERE nom = ?", (aliment["nom"],)
                )
                result = self.cursor.fetchone()
                self.disconnect()

                if result:
                    aliment_id = result[0]
                    self.ajouter_aliment_repas_type(
                        repas_type_id, aliment_id, aliment["quantite"]
                    )
            count += 1
        return count

    def importer_planning(self, planning_data, semaine_id=None):
        """Importe un planning hebdomadaire"""
        if semaine_id is None:
            # Utiliser l'ID de semaine actuel ou en créer un nouveau
            semaines = self.get_semaines_existantes()
            semaine_id = max(semaines) + 1 if semaines else 1

        count = 0
        for jour, repas_list in planning_data.items():
            for repas in repas_list:
                # Créer un nouveau repas
                repas_id = self.ajouter_repas(
                    repas["nom"], jour, repas["ordre"], semaine_id
                )

                # Ajouter les aliments au repas
                for aliment in repas.get("aliments", []):
                    # Chercher l'ID de l'aliment par nom
                    self.connect()
                    self.cursor.execute(
                        "SELECT id FROM aliments WHERE nom = ?", (aliment["nom"],)
                    )
                    result = self.cursor.fetchone()
                    self.disconnect()

                    if result:
                        aliment_id = result[0]
                        self.ajouter_aliment_repas(
                            repas_id, aliment_id, aliment["quantite"]
                        )
                count += 1
        return count
