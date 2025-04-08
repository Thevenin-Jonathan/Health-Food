import unicodedata
import sqlite3
from .db_connector import DBConnector


class AlimentsManager(DBConnector):
    """Gestion des aliments dans la base de données"""

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

    def modifier_aliment(self, aliment_id, data):
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
                aliment_id,
            ),
        )
        self.conn.commit()
        self.disconnect()

    def supprimer_aliment(self, aliment_id):
        """Supprime un aliment et toutes ses références dans les repas"""
        self.connect()

        try:
            # Début d'une transaction explicite
            self.cursor.execute("BEGIN TRANSACTION")

            # Afficher des informations pour déboguer le problème
            print(f"Tentative de suppression de l'aliment avec ID: {aliment_id}")

            # Vérifier si l'aliment existe
            self.cursor.execute(
                "SELECT id, nom FROM aliments WHERE id = ?", (aliment_id,)
            )
            aliment = self.cursor.fetchone()

            if not aliment:
                print(f"Erreur: Aliment avec ID {aliment_id} introuvable.")
                self.conn.rollback()
                self.disconnect()
                return False

            print(f"Aliment trouvé: {aliment['nom']} (ID: {aliment['id']})")

            # Vérifier les références dans les tables
            tables_to_check = [
                ("repas_aliments", "aliment_id"),
                ("repas_types_aliments", "aliment_id"),
            ]

            references = {}
            for table, id_column in tables_to_check:
                self.cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {id_column} = ?", (aliment_id,)
                )
                count = self.cursor.fetchone()[0]
                references[table] = count
                print(f"Références dans {table}: {count}")

            # Supprimer d'abord les références dans les repas_aliments
            if references["repas_aliments"] > 0:
                print(
                    f"Suppression de {references['repas_aliments']} références dans repas_aliments"
                )
                self.cursor.execute(
                    "DELETE FROM repas_aliments WHERE aliment_id = ?", (aliment_id,)
                )

            # Supprimer les références dans les repas_types_aliments
            if references["repas_types_aliments"] > 0:
                print(
                    f"Suppression de {references['repas_types_aliments']} références dans repas_types_aliments"
                )
                self.cursor.execute(
                    "DELETE FROM repas_types_aliments WHERE aliment_id = ?",
                    (aliment_id,),
                )

            # Finalement, supprimer l'aliment lui-même
            print(f"Suppression de l'aliment {aliment_id}")
            self.cursor.execute("DELETE FROM aliments WHERE id = ?", (aliment_id,))

            # Vérifier que l'aliment a bien été supprimé
            self.cursor.execute("SELECT id FROM aliments WHERE id = ?", (aliment_id,))
            if self.cursor.fetchone():
                print(
                    f"⚠️ Erreur: L'aliment {aliment_id} existe toujours après la suppression!"
                )
                self.conn.rollback()
                self.disconnect()
                return False

            # Valider la transaction
            self.conn.commit()
            print(f"✓ Suppression réussie de l'aliment {aliment_id}")
            return True

        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            # En cas d'erreur, afficher le message et annuler la transaction
            print(f"❌ Erreur lors de la suppression de l'aliment {aliment_id}: {e}")
            self.conn.rollback()
            return False

        finally:
            self.disconnect()

    def get_aliments(
        self,
        categorie=None,
        marque=None,
        magasin=None,
        recherche=None,
        sort_column=None,
        sort_order=None,
    ):
        """Récupère tous les aliments avec options de filtrage et de tri"""
        self.connect()
        query = "SELECT * FROM aliments"
        params = []
        conditions = []

        # Collecter les conditions de filtrage standard
        if categorie:
            conditions.append("categorie = ?")
            params.append(categorie)

        if marque:
            conditions.append("marque = ?")
            params.append(marque)

        if magasin:
            conditions.append("magasin = ?")
            params.append(magasin)

        # Récupérer tous les aliments avec les filtres exacts
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Appliquer le tri
        if sort_column:
            numeric_columns = [
                "calories",
                "proteines",
                "glucides",
                "lipides",
                "fibres",
                "prix_kg",
            ]
            if sort_column in numeric_columns:
                query += f' ORDER BY CAST({sort_column} AS REAL) {"ASC" if sort_order else "DESC"}'
            else:
                query += f' ORDER BY {sort_column} COLLATE NOCASE {"ASC" if sort_order else "DESC"}'

        # Exécuter la requête
        self.cursor.execute(query, params)
        results = [dict(row) for row in self.cursor.fetchall()]

        # Filtrer par recherche texte en Python
        if recherche:
            # Normaliser la recherche (supprimer accents et passer en minuscules)
            recherche_norm = self.normalize_text(recherche)

            # Liste pour stocker les résultats filtrés
            filtered_results = []

            # Filtrer chaque aliment
            for item in results:
                # Normaliser tous les champs de texte
                nom_norm = self.normalize_text(item["nom"])
                marque_norm = self.normalize_text(
                    item["marque"] if item["marque"] else ""
                )
                magasin_norm = self.normalize_text(
                    item["magasin"] if item["magasin"] else ""
                )
                categorie_norm = self.normalize_text(
                    item["categorie"] if item["categorie"] else ""
                )

                # Ajouter l'aliment s'il contient le terme dans n'importe quel champ
                if (
                    recherche_norm in nom_norm
                    or recherche_norm in marque_norm
                    or recherche_norm in magasin_norm
                    or recherche_norm in categorie_norm
                ):
                    filtered_results.append(item)

            # Remplacer les résultats par les résultats filtrés
            results = filtered_results

        self.disconnect()
        return results

    def normalize_text(self, text):
        """Normalise le texte en enlevant les accents et en convertissant en minuscules"""
        if not text:
            return ""
        # Décompose les caractères accentués
        text = unicodedata.normalize("NFD", text)
        # Supprime les marques diacritiques
        text = "".join([c for c in text if not unicodedata.combining(c)])
        # Convertit en minuscules
        return text.lower()

    def get_aliments_fallback(
        self,
        categorie=None,
        marque=None,
        magasin=None,
        recherche=None,
        sort_column=None,
        sort_order=None,
    ):
        """Version de secours pour get_aliments sans gestion des accents"""
        self.connect()
        query = "SELECT * FROM aliments"
        params = []
        conditions = []

        # Filtres basiques
        if categorie:
            conditions.append("categorie = ?")
            params.append(categorie)

        if marque:
            conditions.append("marque = ?")
            params.append(marque)

        if magasin:
            conditions.append("magasin = ?")
            params.append(magasin)

        if recherche:
            conditions.append(
                "(nom LIKE ? OR marque LIKE ? OR magasin LIKE ? OR categorie LIKE ?)"
            )
            params.extend(
                [f"%{recherche}%", f"%{recherche}%", f"%{recherche}%", f"%{recherche}%"]
            )

        # Ajouter les conditions à la requête
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Tri standard
        if sort_column:
            numeric_columns = [
                "calories",
                "proteines",
                "glucides",
                "lipides",
                "fibres",
                "prix_kg",
            ]
            if sort_column in numeric_columns:
                query += f' ORDER BY CAST({sort_column} AS REAL) {"ASC" if sort_order else "DESC"}'
            else:
                query += f' ORDER BY {sort_column} COLLATE NOCASE {"ASC" if sort_order else "DESC"}'

        self.cursor.execute(query, params)
        result = [dict(row) for row in self.cursor.fetchall()]

        self.disconnect()
        return result

    def get_aliment(self, aliment_id):
        """Récupère un aliment par son ID"""
        self.connect()
        self.cursor.execute("SELECT * FROM aliments WHERE id = ?", (aliment_id,))
        result = dict(self.cursor.fetchone())
        self.disconnect()
        return result

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
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
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
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
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
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
            print(f"Erreur lors de la récupération des catégories: {e}")
            # Version simple sans tri par fréquence
            self.connect()
            query = "SELECT DISTINCT categorie FROM aliments WHERE categorie IS NOT NULL AND categorie != ''"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.disconnect()
            return [result[0] for result in results if result[0]]
