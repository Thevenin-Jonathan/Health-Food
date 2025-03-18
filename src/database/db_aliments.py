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

    def get_aliments(
        self, categorie=None, recherche=None, sort_column=None, sort_order=None
    ):
        """Récupère tous les aliments avec options de filtrage et de tri"""
        self.connect()
        query = "SELECT * FROM aliments"
        params = []

        # Appliquer les filtres si fournis
        if categorie or recherche:
            query += " WHERE "
            if categorie:
                query += "categorie = ?"
                params.append(categorie)
                if recherche:
                    query += " AND "
            if recherche:
                query += "(nom LIKE ? OR marque LIKE ? OR magasin LIKE ?)"
                params.extend([f"%{recherche}%", f"%{recherche}%", f"%{recherche}%"])

        # Appliquer le tri si demandé
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

        self.cursor.execute(query, params)
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
