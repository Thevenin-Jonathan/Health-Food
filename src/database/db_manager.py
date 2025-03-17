import sqlite3
import os


class DatabaseManager:
    def __init__(self, db_file="nutrition_sportive.db"):
        # S'assurer que le dossier data existe
        os.makedirs("data", exist_ok=True)
        self.db_file = os.path.join("data", db_file)
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        # Activer les contraintes de clés étrangères à chaque connexion
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def init_db(self):
        """Initialise la base de données avec les tables nécessaires"""
        self.connect()

        # Activer les contraintes de clés étrangères (important pour les suppressions en cascade)
        self.cursor.execute("PRAGMA foreign_keys = ON")

        # Table des utilisateurs
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            sexe TEXT,
            age INTEGER,
            taille REAL,
            poids REAL,
            niveau_activite TEXT,
            objectif TEXT,
            taux_variation REAL,
            calories_personnalisees INTEGER,
            repartition_macros TEXT,
            proteines_g_kg REAL,
            glucides_g_kg REAL,
            lipides_g_kg REAL,
            objectif_calories INTEGER,
            objectif_proteines INTEGER,
            objectif_glucides INTEGER,
            objectif_lipides INTEGER
        )
        """
        )

        # Table des aliments
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            marque TEXT,
            magasin TEXT,
            categorie TEXT,
            calories REAL,
            proteines REAL,
            glucides REAL,
            lipides REAL,
            fibres REAL,
            prix_kg REAL
        )
        """
        )

        # Mettre à jour la table des repas pour inclure le numéro de semaine au lieu d'une date
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            jour TEXT NOT NULL,
            ordre INTEGER,
            semaine_id INTEGER DEFAULT NULL
        )
        """
        )

        # Table des aliments dans les repas avec leur quantité
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repas_id INTEGER,
            aliment_id INTEGER,
            quantite REAL,
            FOREIGN KEY (repas_id) REFERENCES repas (id) ON DELETE CASCADE,
            FOREIGN KEY (aliment_id) REFERENCES aliments (id) ON DELETE CASCADE
        )
        """
        )

        # Table des repas types (recettes réutilisables)
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT
        )
        """
        )

        # Table des aliments dans les repas types
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_types_aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repas_type_id INTEGER,
            aliment_id INTEGER,
            quantite REAL,
            FOREIGN KEY (repas_type_id) REFERENCES repas_types (id) ON DELETE CASCADE,
            FOREIGN KEY (aliment_id) REFERENCES aliments (id) ON DELETE CASCADE
        )
        """
        )

        self.conn.commit()
        self.disconnect()

    def ajouter_aliment(self, data):
        """Ajoute un nouvel aliment à la base de données"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO aliments (nom, marque, magasin, categorie, calories, 
                             proteines, glucides, lipides, fibres, prix_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["nom"],
                data["marque"],
                data["magasin"],
                data["categorie"],
                data["calories"],
                data["proteines"],
                data["glucides"],
                data["lipides"],
                data["fibres"],
                data["prix_kg"],
            ),
        )

        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def modifier_aliment(self, id, data):
        """Modifie un aliment existant"""
        self.connect()
        self.cursor.execute(
            """
        UPDATE aliments
        SET nom = ?, marque = ?, magasin = ?, categorie = ?, calories = ?, 
            proteines = ?, glucides = ?, lipides = ?, fibres = ?, prix_kg = ?
        WHERE id = ?
        """,
            (
                data["nom"],
                data["marque"],
                data["magasin"],
                data["categorie"],
                data["calories"],
                data["proteines"],
                data["glucides"],
                data["lipides"],
                data["fibres"],
                data["prix_kg"],
                id,
            ),
        )
        self.conn.commit()
        self.disconnect()

    def supprimer_aliment(self, id):
        """Supprime un aliment et toutes ses références dans les repas"""
        self.connect()

        # Vérifier si l'aliment est utilisé dans des repas
        self.cursor.execute(
            """
            SELECT COUNT(*) FROM repas_aliments
            WHERE aliment_id = ?
            """,
            (id,),
        )
        count_repas = self.cursor.fetchone()[0]

        self.cursor.execute(
            """
            SELECT COUNT(*) FROM repas_types_aliments
            WHERE aliment_id = ?
            """,
            (id,),
        )
        count_repas_types = self.cursor.fetchone()[0]

        # Supprimer d'abord les références dans les repas_aliments
        if count_repas > 0:
            self.cursor.execute(
                "DELETE FROM repas_aliments WHERE aliment_id = ?", (id,)
            )

        # Supprimer les références dans les repas_types_aliments
        if count_repas_types > 0:
            self.cursor.execute(
                "DELETE FROM repas_types_aliments WHERE aliment_id = ?", (id,)
            )

        # Enfin, supprimer l'aliment lui-même
        self.cursor.execute("DELETE FROM aliments WHERE id = ?", (id,))

        # Afficher des informations de débogage
        print(
            f"Suppression de l'aliment {id}. Références supprimées: {count_repas} dans repas, {count_repas_types} dans recettes."
        )

        self.conn.commit()
        self.disconnect()

    def get_aliments(self, sort_column=None, sort_order=None):
        """Récupère tous les aliments avec tri optionnel"""
        self.connect()
        query = "SELECT * FROM aliments"

        if sort_column:
            # Gestion spéciale pour les colonnes numériques pour assurer un tri correct
            numeric_columns = [
                "calories",
                "proteines",
                "glucides",
                "lipides",
                "fibres",
                "prix_kg",
            ]
            if sort_column in numeric_columns:
                # Utiliser CAST pour forcer le tri numérique
                query += f' ORDER BY CAST({sort_column} AS REAL) {"ASC" if sort_order else "DESC"}'
            else:
                # Pour les colonnes texte, utiliser COLLATE NOCASE pour ignorer la casse
                query += f' ORDER BY {sort_column} COLLATE NOCASE {"ASC" if sort_order else "DESC"}'

        self.cursor.execute(query)
        result = [dict(row) for row in self.cursor.fetchall()]
        self.disconnect()
        return result

    def get_aliment(self, id):
        """Récupère un aliment par son ID"""
        self.connect()
        self.cursor.execute("SELECT * FROM aliments WHERE id = ?", (id,))
        result = dict(self.cursor.fetchone())
        self.disconnect()
        return result

    def ajouter_repas(self, nom, jour, ordre, semaine_id=None):
        """Ajoute un nouveau repas avec option de numéro de semaine"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO repas (nom, jour, ordre, semaine_id)
        VALUES (?, ?, ?, ?)
        """,
            (nom, jour, ordre, semaine_id),
        )

        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def ajouter_aliment_repas(self, repas_id, aliment_id, quantite):
        """Ajoute un aliment à un repas avec sa quantité"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO repas_aliments (repas_id, aliment_id, quantite)
        VALUES (?, ?, ?)
        """,
            (repas_id, aliment_id, quantite),
        )

        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def supprimer_aliment_repas(self, repas_id, aliment_id):
        """Supprime un aliment d'un repas"""
        self.connect()
        self.cursor.execute(
            "DELETE FROM repas_aliments WHERE repas_id = ? AND aliment_id = ?",
            (repas_id, aliment_id),
        )
        self.conn.commit()
        self.disconnect()

    def get_aliments_repas(self, repas_id):
        """Récupère tous les aliments d'un repas avec leur quantité"""
        self.connect()
        self.cursor.execute(
            """
            SELECT ra.id as relation_id, ra.quantite, a.* 
            FROM repas_aliments ra
            JOIN aliments a ON ra.aliment_id = a.id
            WHERE ra.repas_id = ?
            ORDER BY a.nom
            """,
            (repas_id,),
        )
        result = [dict(row) for row in self.cursor.fetchall()]
        self.disconnect()
        return result

    def get_repas_semaine(self, semaine_id=None):
        """Récupère tous les repas d'une semaine spécifique avec leurs aliments"""
        self.connect()
        jours = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]
        result = {jour: [] for jour in jours}

        # Récupérer tous les repas de la semaine spécifiée (ou sans numéro de semaine si None)
        if semaine_id is not None:
            # Récupérer les repas pour la semaine spécifique
            self.cursor.execute(
                """
                SELECT * FROM repas 
                WHERE semaine_id = ? 
                ORDER BY jour, ordre
                """,
                (semaine_id,),
            )
        else:
            # Récupérer les repas sans numéro de semaine (comportement historique)
            self.cursor.execute(
                """
                SELECT * FROM repas 
                WHERE semaine_id IS NULL 
                ORDER BY jour, ordre
                """
            )

        repas_list = [dict(row) for row in self.cursor.fetchall()]

        for repas in repas_list:
            # Récupérer les aliments pour ce repas
            self.cursor.execute(
                """
            SELECT ra.quantite, a.* 
            FROM repas_aliments ra
            JOIN aliments a ON ra.aliment_id = a.id
            WHERE ra.repas_id = ?
            """,
                (repas["id"],),
            )

            aliments = [dict(row) for row in self.cursor.fetchall()]
            repas["aliments"] = aliments

            # Calculer les totaux du repas
            repas["total_calories"] = sum(
                a["calories"] * a["quantite"] / 100 for a in aliments
            )
            repas["total_proteines"] = sum(
                a["proteines"] * a["quantite"] / 100 for a in aliments
            )
            repas["total_glucides"] = sum(
                a["glucides"] * a["quantite"] / 100 for a in aliments
            )
            repas["total_lipides"] = sum(
                a["lipides"] * a["quantite"] / 100 for a in aliments
            )

            result[repas["jour"]].append(repas)

        self.disconnect()
        return result

    def generer_liste_courses(self, semaine_id=None):
        """Génère une liste de courses organisée par magasin et catégorie pour une semaine spécifique"""
        self.connect()

        # Requête conditionnelle selon si une semaine est spécifiée
        if semaine_id is not None:
            self.cursor.execute(
                """
            SELECT a.*, ra.quantite, a.magasin, a.categorie, a.prix_kg 
            FROM repas_aliments ra
            JOIN aliments a ON ra.aliment_id = a.id
            JOIN repas r ON ra.repas_id = r.id
            WHERE r.semaine_id = ?
            ORDER BY a.magasin, a.categorie, a.nom
            """,
                (semaine_id,),
            )
        else:
            # Si pas de semaine spécifiée, récupérer tous les aliments
            self.cursor.execute(
                """
            SELECT a.*, ra.quantite, a.magasin, a.categorie, a.prix_kg 
            FROM repas_aliments ra
            JOIN aliments a ON ra.aliment_id = a.id
            ORDER BY a.magasin, a.categorie, a.nom
            """
            )

        aliments = [dict(row) for row in self.cursor.fetchall()]

        # Organiser par magasin et catégorie
        liste_courses = {}
        for aliment in aliments:
            magasin = aliment["magasin"] or "Non spécifié"
            categorie = aliment["categorie"] or "Non spécifiée"

            if magasin not in liste_courses:
                liste_courses[magasin] = {}

            if categorie not in liste_courses[magasin]:
                liste_courses[magasin][categorie] = []

            # Vérifier si l'aliment existe déjà dans la liste
            aliment_existe = False
            for item in liste_courses[magasin][categorie]:
                if item["id"] == aliment["id"]:
                    item["quantite"] += aliment["quantite"]
                    aliment_existe = True
                    break

            if not aliment_existe:
                liste_courses[magasin][categorie].append(aliment)

        self.disconnect()
        return liste_courses

    def supprimer_repas(self, repas_id):
        """Supprime un repas et ses aliments associés"""
        self.connect()
        self.cursor.execute("DELETE FROM repas WHERE id = ?", (repas_id,))
        self.conn.commit()
        self.disconnect()

    def supprimer_semaine(self, semaine_id):
        """Supprime tous les repas associés à une semaine spécifique"""
        print(f"Suppression en DB de la semaine {semaine_id}")  # Log pour débugger
        self.connect()

        # Compter le nombre de repas avant suppression
        self.cursor.execute(
            "SELECT COUNT(*) FROM repas WHERE semaine_id = ?", (semaine_id,)
        )
        count_before = self.cursor.fetchone()[0]
        print(f"Nombre de repas à supprimer : {count_before}")  # Log pour débugger

        # Exécuter la suppression
        self.cursor.execute("DELETE FROM repas WHERE semaine_id = ?", (semaine_id,))

        # Vérifier le nombre de lignes affectées
        rows_affected = self.cursor.rowcount
        print(f"Nombre de repas supprimés : {rows_affected}")  # Log pour débugger

        self.conn.commit()
        self.disconnect()

        return rows_affected

    # Méthodes pour gérer les repas types
    def ajouter_repas_type(self, nom, description):
        """Ajoute un nouveau repas type (recette)"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO repas_types (nom, description)
        VALUES (?, ?)
        """,
            (nom, description),
        )

        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def ajouter_aliment_repas_type(self, repas_type_id, aliment_id, quantite):
        """Ajoute un aliment à un repas type avec sa quantité"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO repas_types_aliments (repas_type_id, aliment_id, quantite)
        VALUES (?, ?, ?)
        """,
            (repas_type_id, aliment_id, quantite),
        )

        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def supprimer_aliment_repas_type(self, repas_type_id, aliment_id):
        """Supprime un aliment d'un repas type"""
        self.connect()
        self.cursor.execute(
            "DELETE FROM repas_types_aliments WHERE repas_type_id = ? AND aliment_id = ?",
            (repas_type_id, aliment_id),
        )
        self.conn.commit()
        self.disconnect()

    def get_repas_types(self):
        """Récupère tous les repas types"""
        self.connect()
        self.cursor.execute("SELECT * FROM repas_types ORDER BY nom")
        result = [dict(row) for row in self.cursor.fetchall()]

        # Récupérer les aliments et calculer les totaux pour chaque repas type
        for repas_type in result:
            self.cursor.execute(
                """
            SELECT rta.quantite, a.* 
            FROM repas_types_aliments rta
            JOIN aliments a ON rta.aliment_id = a.id
            WHERE rta.repas_type_id = ?
            """,
                (repas_type["id"],),
            )

            aliments = [dict(row) for row in self.cursor.fetchall()]
            repas_type["aliments"] = aliments

            # Calculer les totaux du repas
            repas_type["total_calories"] = sum(
                a["calories"] * a["quantite"] / 100 for a in aliments
            )
            repas_type["total_proteines"] = sum(
                a["proteines"] * a["quantite"] / 100 for a in aliments
            )
            repas_type["total_glucides"] = sum(
                a["glucides"] * a["quantite"] / 100 for a in aliments
            )
            repas_type["total_lipides"] = sum(
                a["lipides"] * a["quantite"] / 100 for a in aliments
            )

        self.disconnect()
        return result

    def get_repas_type(self, id):
        """Récupère un repas type par son ID avec ses aliments"""
        self.connect()
        self.cursor.execute("SELECT * FROM repas_types WHERE id = ?", (id,))
        result = dict(self.cursor.fetchone())

        # Récupérer les aliments pour ce repas type
        self.cursor.execute(
            """
        SELECT rta.quantite, a.* 
        FROM repas_types_aliments rta
        JOIN aliments a ON rta.aliment_id = a.id
        WHERE rta.repas_type_id = ?
        """,
            (id,),
        )

        aliments = [dict(row) for row in self.cursor.fetchall()]
        result["aliments"] = aliments

        # Calculer les totaux nutritionnels
        result["total_calories"] = sum(
            a["calories"] * a["quantite"] / 100 for a in aliments
        )
        result["total_proteines"] = sum(
            a["proteines"] * a["quantite"] / 100 for a in aliments
        )
        result["total_glucides"] = sum(
            a["glucides"] * a["quantite"] / 100 for a in aliments
        )
        result["total_lipides"] = sum(
            a["lipides"] * a["quantite"] / 100 for a in aliments
        )

        self.disconnect()
        return result

    def supprimer_repas_type(self, id):
        """Supprime un repas type et ses aliments associés"""
        self.connect()
        self.cursor.execute("DELETE FROM repas_types WHERE id = ?", (id,))
        self.conn.commit()
        self.disconnect()

    def appliquer_repas_type_au_jour(self, repas_type_id, jour, ordre, semaine_id=None):
        """Applique un repas type à un jour spécifique d'une semaine donnée"""
        repas_type = self.get_repas_type(repas_type_id)

        # Créer le repas avec le numéro de semaine
        repas_id = self.ajouter_repas(repas_type["nom"], jour, ordre, semaine_id)

        # Ajouter tous les aliments du repas type au nouveau repas
        for aliment in repas_type["aliments"]:
            self.ajouter_aliment_repas(repas_id, aliment["id"], aliment["quantite"])

        return repas_id

    def modifier_quantite_aliment_repas_type(self, repas_type_id, aliment_id, quantite):
        """Modifie la quantité d'un aliment dans un repas type"""
        self.connect()
        self.cursor.execute(
            """
        UPDATE repas_types_aliments 
        SET quantite = ? 
        WHERE repas_type_id = ? AND aliment_id = ?
        """,
            (quantite, repas_type_id, aliment_id),
        )
        self.conn.commit()
        self.disconnect()

    def modifier_repas_type(self, id, nom, description):
        """Modifie un repas type existant"""
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas_types
            SET nom = ?, description = ?
            WHERE id = ?
            """,
            (nom, description, id),
        )
        self.conn.commit()
        self.disconnect()

    def appliquer_repas_type_au_jour_avec_facteurs(
        self, repas_type_id, jour, ordre, semaine_id=None, facteurs_quantite=None
    ):
        """Applique un repas type à un jour spécifique en ajustant les quantités"""
        if facteurs_quantite is None:
            facteurs_quantite = {}

        repas_type = self.get_repas_type(repas_type_id)

        # Créer le repas avec le numéro de semaine
        repas_id = self.ajouter_repas(repas_type["nom"], jour, ordre, semaine_id)

        # Ajouter tous les aliments du repas type au nouveau repas avec les quantités ajustées
        for aliment in repas_type["aliments"]:
            facteur = facteurs_quantite.get(
                aliment["id"], 1.0
            )  # 1.0 par défaut si pas de facteur
            quantite_ajustee = aliment["quantite"] * facteur
            self.ajouter_aliment_repas(repas_id, aliment["id"], quantite_ajustee)

        return repas_id

    def appliquer_recette_modifiee_au_jour(
        self, recette_base_id, liste_ingredients, jour, ordre, semaine_id=None
    ):
        """Applique une recette modifiée à un jour spécifique"""
        # Récupérer la recette de base pour avoir son nom
        recette_base = self.get_repas_type(recette_base_id)

        # Créer le repas avec le numéro de semaine
        repas_id = self.ajouter_repas(recette_base["nom"], jour, ordre, semaine_id)

        # Ajouter tous les ingrédients avec les bonnes quantités
        for ingredient in liste_ingredients:
            self.ajouter_aliment_repas(
                repas_id, ingredient["id"], ingredient["quantite"]
            )

        return repas_id

    def get_marques_uniques(self):
        """Récupère toutes les marques uniques présentes dans la base de données, triées par fréquence"""
        try:
            self.connect()
            query = """
                SELECT marque, COUNT(*) as count 
                FROM aliments 
                WHERE marque IS NOT NULL AND marque != '' 
                GROUP BY marque 
                ORDER BY count DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]
        except Exception as e:
            print(f"Erreur lors de la récupération des marques: {e}")
            # Version simple sans tri par fréquence
            self.connect()
            query = "SELECT DISTINCT marque FROM aliments WHERE marque IS NOT NULL AND marque != ''"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]

    def get_magasins_uniques(self):
        """Récupère tous les magasins uniques présents dans la base de données, triés par fréquence"""
        try:
            self.connect()
            query = """
                SELECT magasin, COUNT(*) as count 
                FROM aliments 
                WHERE magasin IS NOT NULL AND magasin != '' 
                GROUP BY magasin 
                ORDER BY count DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]
        except Exception as e:
            print(f"Erreur lors de la récupération des magasins: {e}")
            # Version simple sans tri par fréquence
            self.connect()
            query = "SELECT DISTINCT magasin FROM aliments WHERE magasin IS NOT NULL AND magasin != ''"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]

    def get_categories_uniques(self):
        """Récupère toutes les catégories uniques présentes dans la base de données, triées par fréquence"""
        try:
            self.connect()
            query = """
                SELECT categorie, COUNT(*) as count 
                FROM aliments 
                WHERE categorie IS NOT NULL AND categorie != '' 
                GROUP BY categorie 
                ORDER BY count DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]
        except Exception as e:
            print(f"Erreur lors de la récupération des catégories: {e}")
            # Version simple sans tri par fréquence
            self.connect()
            query = "SELECT DISTINCT categorie FROM aliments WHERE categorie IS NOT NULL AND categorie != ''"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]

    # Méthodes pour gérer les données utilisateur
    def sauvegarder_utilisateur(self, data):
        """Sauvegarde ou met à jour les informations utilisateur"""
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
                    objectif, taux_variation, calories_personnalisees, repartition_macros,
                    proteines_g_kg, glucides_g_kg, lipides_g_kg,
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
                    data.get("repartition_macros", "Standard"),
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
                    calories_personnalisees = ?, repartition_macros = ?,
                    proteines_g_kg = ?, glucides_g_kg = ?, lipides_g_kg = ?,
                    objectif_calories = ?, objectif_proteines = ?, objectif_glucides = ?, objectif_lipides = ?
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
                    data.get("repartition_macros", "Standard"),
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
        """Récupère les informations de l'utilisateur"""
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
                "repartition_macros": "Standard",
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
        """Calcule les besoins caloriques journaliers basés sur les données utilisateur"""
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
            # Convertir g/semaine en déficit calorique journalier
            # 100g de graisse = environ 770 kcal (mis à jour selon les nouvelles valeurs)
            ajustement_calories = -(taux_variation * 110)
        elif objectif == "Prise de masse":
            ajustement_calories = taux_variation * 110

        calories_objectif = calories_maintien + ajustement_calories

        # Si des calories personnalisées sont définies, les utiliser
        calories_perso = user_data.get("calories_personnalisees", 0)
        if calories_perso > 0:
            calories_finales = calories_perso
        else:
            calories_finales = calories_objectif

        # Calculer la répartition des macros
        repartition = user_data.get("repartition_macros", "Standard")
        if repartition == "Standard":
            proteines_pct = 0.3
            glucides_pct = 0.4
            lipides_pct = 0.3
        elif repartition == "Low-carb":
            proteines_pct = 0.35
            glucides_pct = 0.25
            lipides_pct = 0.4
        elif repartition == "Hyperprotéiné":
            proteines_pct = 0.45
            glucides_pct = 0.35
            lipides_pct = 0.2
        elif repartition == "Faible en gras":
            proteines_pct = 0.35
            glucides_pct = 0.5
            lipides_pct = 0.15
        elif repartition == "Cétogène":
            proteines_pct = 0.30
            glucides_pct = 0.05
            lipides_pct = 0.65
        elif repartition == "Personnalisé":
            # Ces valeurs seraient stockées ailleurs dans un cas réel
            proteines_pct = user_data.get("proteines_pct", 0.3)
            glucides_pct = user_data.get("glucides_pct", 0.4)
            lipides_pct = user_data.get("lipides_pct", 0.3)
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
