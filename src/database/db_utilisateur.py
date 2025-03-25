from .db_connector import DBConnector


class UserManager(DBConnector):
    """
    Gestion des utilisateurs dans la base de données.
    Cette classe gère le profil utilisateur et les calculs nutritionnels.
    """

    def creer_utilisateur_par_defaut_si_necessaire(self):
        """Crée un utilisateur par défaut si aucun n'existe dans la base de données"""
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

    def sauvegarder_utilisateur(self, data):
        """
        Sauvegarde ou met à jour les informations utilisateur

        Args:
            data (dict): Dictionnaire contenant les données de l'utilisateur
        """
        self.connect()

        # Vérifier si un utilisateur existe déjà (on ne garde qu'un seul profil)
        self.cursor.execute("SELECT COUNT(*) FROM utilisateur")
        count = self.cursor.fetchone()[0]

        if count == 0:
            # Insertion d'un nouvel utilisateur
            self.cursor.execute(
                """
                INSERT INTO utilisateur (
                    nom, sexe, age, taille, poids, niveau_activite, 
                    objectif, taux_variation, calories_personnalisees,
                    regime_alimentaire, proteines_g_kg, glucides_g_kg, lipides_g_kg,
                    objectif_calories, objectif_proteines, objectif_glucides, objectif_lipides
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.get("nom", ""),
                    data.get("sexe", ""),
                    data.get("age", 0),
                    data.get("taille", 0),
                    data.get("poids", 0),
                    data.get("niveau_activite", "Sédentaire"),
                    data.get("objectif", "Maintien"),
                    data.get("taux_variation", 0),
                    data.get("calories_personnalisees", 0),
                    data.get("regime_alimentaire", "Régime équilibré"),
                    data.get("proteines_g_kg", 1.2),
                    data.get("glucides_g_kg", 3.0),
                    data.get("lipides_g_kg", 0.8),
                    data.get("objectif_calories", 0),
                    data.get("objectif_proteines", 0),
                    data.get("objectif_glucides", 0),
                    data.get("objectif_lipides", 0),
                ),
            )
        else:
            # Mise à jour de l'utilisateur existant (on prend le premier)
            self.cursor.execute("SELECT id FROM utilisateur LIMIT 1")
            user_id = self.cursor.fetchone()[0]

            self.cursor.execute(
                """
                UPDATE utilisateur SET
                    nom = ?, sexe = ?, age = ?, taille = ?, poids = ?,
                    niveau_activite = ?, objectif = ?, taux_variation = ?,
                    calories_personnalisees = ?, regime_alimentaire = ?, proteines_g_kg = ?, glucides_g_kg = ?,
                    lipides_g_kg = ?, objectif_calories = ?, objectif_proteines = ?, objectif_glucides = ?, objectif_lipides = ?
                WHERE id = ?
                """,
                (
                    data.get("nom", ""),
                    data.get("sexe", ""),
                    data.get("age", 0),
                    data.get("taille", 0),
                    data.get("poids", 0),
                    data.get("niveau_activite", "Sédentaire"),
                    data.get("objectif", "Maintien"),
                    data.get("taux_variation", 0),
                    data.get("calories_personnalisees", 0),
                    data.get("regime_alimentaire", "Régime équilibré"),
                    data.get("proteines_g_kg", 1.2),
                    data.get("glucides_g_kg", 3.0),
                    data.get("lipides_g_kg", 0.8),
                    data.get("objectif_calories", 0),
                    data.get("objectif_proteines", 0),
                    data.get("objectif_glucides", 0),
                    data.get("objectif_lipides", 0),
                    user_id,
                ),
            )

        self.conn.commit()
        self.disconnect()

    def get_utilisateur(self):
        """
        Récupère les informations de l'utilisateur

        Returns:
            dict: Les données de l'utilisateur ou valeurs par défaut si aucun utilisateur n'existe
        """
        self.connect()
        self.cursor.execute("SELECT COUNT(*) FROM utilisateur")
        count = self.cursor.fetchone()[0]

        if count == 0:
            # Retourner des valeurs par défaut si aucun utilisateur n'est trouvé
            self.disconnect()
            return {
                "nom": "",
                "sexe": "Homme",
                "age": 30,
                "taille": 175,
                "poids": 70,
                "niveau_activite": "Modéré",
                "objectif": "Maintien",
                "taux_variation": 0,
                "calories_personnalisees": 0,
                "regime_alimentaire": "Régime équilibré",
                "proteines_g_kg": 1.2,
                "glucides_g_kg": 3.0,
                "lipides_g_kg": 0.8,
                "objectif_calories": 0,
                "objectif_proteines": 0,
                "objectif_glucides": 0,
                "objectif_lipides": 0,
            }

        self.cursor.execute("SELECT * FROM utilisateur LIMIT 1")
        user = dict(self.cursor.fetchone())
        self.disconnect()
        return user

    def calculer_calories_journalieres(self, user_data=None):
        """
        Calcule les besoins caloriques journaliers basés sur les données utilisateur

        Args:
            user_data (dict, optional): Données utilisateur. Si None, les données seront récupérées de la BD

        Returns:
            dict: Les résultats des calculs nutritionnels
        """
        if user_data is None:
            user_data = self.get_utilisateur()

        # Facteurs d'activité ajustés pour des résultats plus réalistes
        facteurs_activite = {
            "Très sédentaire": 1.0,
            "Sédentaire": 1.1,  # Sédentaire (aucun exercice)
            "Légèrement actif": 1.2,  # Exercice 1-3 jours/semaine
            "Peu actif": 1.375,  # Intermédiaire
            "Modéré": 1.55,  # Exercice 3-5 jours/semaine
            "Actif": 1.725,  # Entraînements réguliers
            "Très actif": 1.9,  # Activité intense quotidienne
            "Extrêmement actif": 2.1,  # Sport d'élite ou travail très exigeant
            "Ultra-intense": 2.3,  # Entraînement plusieurs fois par jour
        }

        # Calcul du métabolisme de base (MB) selon Harris-Benedict
        poids = user_data.get("poids", 70)
        taille = user_data.get("taille", 175)
        age = user_data.get("age", 30)
        sexe = user_data.get("sexe", "Homme")
        if sexe == "Homme":
            mb = (10 * poids) + (6.25 * taille) - (5 * age) + 5
        else:
            mb = (10 * poids) + (6.25 * taille) - (5 * age) - 161

        # Appliquer le facteur d'activité
        niveau_activite = user_data.get("niveau_activite", "Modéré")
        facteur = facteurs_activite.get(niveau_activite, 1.55)
        calories_maintien = mb * facteur

        # Ajuster selon l'objectif
        objectif = user_data.get("objectif", "Maintien")
        taux_variation = user_data.get("taux_variation", 0)  # en g/semaine
        ajustement_calories = 0
        if objectif == "Perte de poids":
            # taux_variation est en g/semaine
            # 1kg de graisse = 7700 kcal, donc 1g = 7.7 kcal
            # Division par 7 pour obtenir le déficit journalier
            ajustement_calories = -(taux_variation * 7.7) / 7
        elif objectif == "Prise de masse":
            # Même calcul pour le surplus calorique
            ajustement_calories = (taux_variation * 7.7) / 7

        calories_objectif = calories_maintien + ajustement_calories

        # Si des calories personnalisées sont définies, les utiliser
        calories_perso = user_data.get("calories_personnalisees", 0)
        if calories_perso > 0:
            calories_finales = calories_perso
        else:
            calories_finales = calories_objectif

        # Utiliser le régime alimentaire pour déterminer la répartition des macros
        regime = user_data.get("regime_alimentaire", "Régime équilibré")

        # Mapper les régimes aux répartitions
        if regime == "Régime équilibré":
            proteines_pct = 0.3
            glucides_pct = 0.4
            lipides_pct = 0.3
        elif regime == "Régime hypocalorique":
            proteines_pct = 0.35
            glucides_pct = 0.35
            lipides_pct = 0.3
        elif regime == "Régime hyperprotéiné":
            proteines_pct = 0.45
            glucides_pct = 0.35
            lipides_pct = 0.2
        elif regime == "Régime cétogène":
            proteines_pct = 0.30
            glucides_pct = 0.05
            lipides_pct = 0.65
        elif regime == "Régime de prise de masse":
            proteines_pct = 0.35
            glucides_pct = 0.45
            lipides_pct = 0.2
        elif regime == "Régime végétarien / vegan":
            proteines_pct = 0.25
            glucides_pct = 0.5
            lipides_pct = 0.25
        elif regime == "Personnalisé":
            # Utiliser les valeurs personnalisées stockées
            proteines_g_kg = user_data.get("proteines_g_kg", 1.2)
            glucides_g_kg = user_data.get("glucides_g_kg", 3.0)
            lipides_g_kg = user_data.get("lipides_g_kg", 0.8)

            # Calcul des grammes totaux basés sur le poids
            proteines_g_total = proteines_g_kg * poids
            glucides_g_total = glucides_g_kg * poids
            lipides_g_total = lipides_g_kg * poids

            # Calcul des calories pour chaque macro
            calories_proteines = proteines_g_total * 4
            calories_glucides = glucides_g_total * 4
            calories_lipides = lipides_g_total * 9

            # Calcul des pourcentages
            total_calories = calories_proteines + calories_glucides + calories_lipides
            proteines_pct = calories_proteines / total_calories
            glucides_pct = calories_glucides / total_calories
            lipides_pct = calories_lipides / total_calories

            return {
                "metabolisme_base": round(mb),
                "calories_maintien": round(calories_maintien),
                "calories_objectif": round(calories_objectif),
                "calories_finales": round(calories_finales),
                "proteines_g": round(proteines_g_total),
                "glucides_g": round(glucides_g_total),
                "lipides_g": round(lipides_g_total),
                "proteines_pct": proteines_pct,
                "glucides_pct": glucides_pct,
                "lipides_pct": lipides_pct,
            }
        else:
            # Valeurs par défaut
            proteines_pct = 0.3
            glucides_pct = 0.4
            lipides_pct = 0.3

        # Calcul des macros en grammes
        # 1g de protéines = 4 kcal, 1g de glucides = 4 kcal, 1g de lipides = 9 kcal
        proteines_g = (calories_finales * proteines_pct) / 4
        glucides_g = (calories_finales * glucides_pct) / 4
        lipides_g = (calories_finales * lipides_pct) / 9

        return {
            "metabolisme_base": round(mb),
            "calories_maintien": round(calories_maintien),
            "calories_objectif": round(calories_objectif),
            "calories_finales": round(calories_finales),
            "proteines_g": round(proteines_g),
            "glucides_g": round(glucides_g),
            "lipides_g": round(lipides_g),
            "proteines_pct": proteines_pct,
            "glucides_pct": glucides_pct,
            "lipides_pct": lipides_pct,
        }

    # Dans UserManager, ajouter ces méthodes
    def save_user_theme(self, theme_name):
        """Sauvegarde le thème choisi par l'utilisateur"""
        self.connect()

        # Vérifier s'il existe un utilisateur
        self.cursor.execute("SELECT id FROM utilisateur LIMIT 1")
        user = self.cursor.fetchone()

        if user:
            # Mettre à jour le thème
            self.cursor.execute(
                "UPDATE utilisateur SET theme_actif = ? WHERE id = ?",
                (theme_name, user["id"]),
            )
        else:
            # Créer un utilisateur avec le thème par défaut
            self.cursor.execute(
                "INSERT INTO utilisateur (theme_actif) VALUES (?)", (theme_name,)
            )

        self.conn.commit()
        self.disconnect()
        return True

    def get_user_theme(self):
        """Récupère le thème de l'utilisateur"""
        self.connect()
        self.cursor.execute("SELECT theme_actif FROM utilisateur LIMIT 1")
        result = self.cursor.fetchone()
        self.disconnect()

        if result and result["theme_actif"]:
            return result["theme_actif"]
        return "Vert Nature"  # Thème par défaut
