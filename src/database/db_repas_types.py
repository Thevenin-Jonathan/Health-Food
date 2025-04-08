from .db_connector import DBConnector


class RepasTypesManager(DBConnector):
    """Gestion des repas types (recettes) dans la base de données"""

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

    def get_repas_type(self, repas_type_id):
        """Récupère un repas type par son ID avec ses aliments"""
        self.connect()
        self.cursor.execute("SELECT * FROM repas_types WHERE id = ?", (repas_type_id,))
        result = dict(self.cursor.fetchone())

        # Récupérer les aliments pour ce repas type
        self.cursor.execute(
            """
        SELECT rta.quantite, a.* 
        FROM repas_types_aliments rta
        JOIN aliments a ON rta.aliment_id = a.id
        WHERE rta.repas_type_id = ?
        """,
            (repas_type_id,),
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

    def supprimer_repas_type(self, repas_type_id):
        """Supprime un repas type et ses aliments associés"""
        self.connect()
        self.cursor.execute("DELETE FROM repas_types WHERE id = ?", (repas_type_id,))
        self.conn.commit()
        self.disconnect()

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

    def modifier_repas_type(self, repas_type_id, nom, description):
        """Modifie un repas type existant"""
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas_types
            SET nom = ?, description = ?
            WHERE id = ?
            """,
            (nom, description, repas_type_id),
        )
        self.conn.commit()
        self.disconnect()

    def appliquer_repas_type_au_jour(
        self, repas_type_id, jour, ordre, semaine_id=None, nom_personnalise=None
    ):
        """Applique un repas type à un jour spécifique d'une semaine donnée

        Args:
            repas_type_id: ID du repas type à appliquer
            jour: Jour de la semaine
            ordre: Ordre du repas dans la journée
            semaine_id: ID de la semaine (optionnel)
            nom_personnalise: Nom personnalisé pour le repas (optionnel)

        Returns:
            ID du repas créé
        """
        from .db_repas import RepasManager  # pylint: disable=import-outside-toplevel

        repas_manager = RepasManager(self.db_file)
        repas_type = self.get_repas_type(repas_type_id)

        # Utiliser le nom personnalisé s'il est fourni, sinon utiliser le nom de la recette
        nom_repas = nom_personnalise if nom_personnalise else repas_type["nom"]

        # Créer le repas avec le numéro de semaine et le nom approprié
        # Important : ajouter aussi l'ID de la recette pour pouvoir suivre les modifications
        repas_id = repas_manager.ajouter_repas(
            nom_repas,
            jour,
            ordre,
            semaine_id,
            repas_type_id,  # Stocker l'ID de la recette dans le repas
        )

        # Ajouter tous les aliments du repas type au nouveau repas
        for aliment in repas_type["aliments"]:
            repas_manager.ajouter_aliment_repas(
                repas_id, aliment["id"], aliment["quantite"]
            )

        return repas_id

    def appliquer_repas_type_au_jour_avec_facteurs(
        self, repas_type_id, jour, ordre, semaine_id=None, facteurs_quantite=None
    ):
        """Applique un repas type à un jour spécifique en ajustant les quantités"""
        from .db_repas import RepasManager  # pylint: disable=import-outside-toplevel

        repas_manager = RepasManager(self.db_file)

        if facteurs_quantite is None:
            facteurs_quantite = {}

        repas_type = self.get_repas_type(repas_type_id)

        # Créer le repas avec le numéro de semaine
        repas_id = repas_manager.ajouter_repas(
            repas_type["nom"], jour, ordre, semaine_id
        )

        # Ajouter tous les aliments du repas type au nouveau repas avec les quantités ajustées
        for aliment in repas_type["aliments"]:
            facteur = facteurs_quantite.get(
                aliment["id"], 1.0
            )  # 1.0 par défaut si pas de facteur
            quantite_ajustee = aliment["quantite"] * facteur
            repas_manager.ajouter_aliment_repas(
                repas_id, aliment["id"], quantite_ajustee
            )

        return repas_id

    def appliquer_recette_modifiee_au_jour(
        self, recette_base_id, liste_ingredients, jour, ordre, semaine_id=None
    ):
        """Applique une recette modifiée à un jour spécifique"""
        from .db_repas import RepasManager  # pylint: disable=import-outside-toplevel

        repas_manager = RepasManager(self.db_file)

        # Récupérer la recette de base pour avoir son nom
        recette_base = self.get_repas_type(recette_base_id)

        # Créer le repas avec le numéro de semaine
        repas_id = repas_manager.ajouter_repas(
            recette_base["nom"], jour, ordre, semaine_id
        )

        # Ajouter tous les ingrédients avec les bonnes quantités
        for ingredient in liste_ingredients:
            repas_manager.ajouter_aliment_repas(
                repas_id, ingredient["id"], ingredient["quantite"]
            )

        return repas_id
