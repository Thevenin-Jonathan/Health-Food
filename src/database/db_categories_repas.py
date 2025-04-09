from .db_connector import DBConnector


class CategoriesRepasManager(DBConnector):
    """Gestion des catégories de repas dans la base de données"""

    def ajouter_categorie(self, nom, couleur="#3498db"):
        """Ajoute une nouvelle catégorie de repas"""
        self.connect()
        self.cursor.execute(
            "INSERT INTO categories_repas (nom, couleur) VALUES (?, ?)", (nom, couleur)
        )
        last_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return last_id

    def modifier_categorie(self, categorie_id, nom, couleur):
        """Modifie une catégorie existante"""
        self.connect()
        self.cursor.execute(
            "UPDATE categories_repas SET nom = ?, couleur = ? WHERE id = ?",
            (nom, couleur, categorie_id),
        )
        rows_affected = self.cursor.rowcount > 0
        self.conn.commit()
        self.disconnect()
        return rows_affected

    def supprimer_categorie(self, categorie_id):
        """Supprime une catégorie de repas"""
        self.connect()
        self.cursor.execute(
            "UPDATE repas_types SET categorie_id = NULL WHERE categorie_id = ?",
            (categorie_id,),
        )

        self.cursor.execute(
            "DELETE FROM categories_repas WHERE id = ?", (categorie_id,)
        )
        rows_affected = self.cursor.rowcount > 0
        self.conn.commit()
        self.disconnect()
        return rows_affected

    def get_categories(self):
        """Récupère toutes les catégories de repas"""
        self.connect()
        self.cursor.execute("SELECT * FROM categories_repas ORDER BY nom")
        result = [dict(row) for row in self.cursor.fetchall()]
        self.disconnect()
        return result

    def get_categorie(self, categorie_id):
        """Récupère une catégorie de repas par son ID"""
        self.connect()
        self.cursor.execute(
            "SELECT * FROM categories_repas WHERE id = ?", (categorie_id,)
        )
        row = self.cursor.fetchone()
        self.disconnect()
        return dict(row) if row else None
