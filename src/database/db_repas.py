from .db_connector import DBConnector


class RepasManager(DBConnector):
    """Gestion des repas dans la base de données"""

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

    def modifier_quantite_aliment_repas(self, repas_id, aliment_id, quantite):
        """Modifie la quantité d'un aliment dans un repas"""
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas_aliments 
            SET quantite = ? 
            WHERE repas_id = ? AND aliment_id = ?
            """,
            (quantite, repas_id, aliment_id),
        )
        self.conn.commit()
        rows_affected = self.cursor.rowcount > 0
        self.disconnect()
        return rows_affected

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

    def get_semaines_existantes(self):
        """Récupère tous les IDs de semaines qui existent dans la base de données"""
        self.connect()
        self.cursor.execute(
            """
            SELECT DISTINCT semaine_id FROM repas
            WHERE semaine_id IS NOT NULL
            ORDER BY semaine_id
            """
        )
        semaines = [row[0] for row in self.cursor.fetchall()]  # Renvoie une liste d'IDs
        self.disconnect()
        return semaines

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
        self.connect()

        # Exécuter la suppression
        self.cursor.execute("DELETE FROM repas WHERE semaine_id = ?", (semaine_id,))

        # Vérifier le nombre de lignes affectées
        rows_affected = self.cursor.rowcount

        self.conn.commit()
        self.disconnect()

        return rows_affected

    def changer_jour_repas(self, repas_id, nouveau_jour, nouvel_ordre):
        """Change le jour et l'ordre d'un repas"""
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas
            SET jour = ?, ordre = ?
            WHERE id = ?
            """,
            (nouveau_jour, nouvel_ordre, repas_id),
        )
        # Stocker le nombre de lignes affectées avant de fermer la connexion
        rows_affected = self.cursor.rowcount
        self.conn.commit()
        self.disconnect()
        return rows_affected > 0

    def modifier_nom_repas(self, repas_id, nouveau_nom):
        """Modifie le nom d'un repas existant"""
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas
            SET nom = ?
            WHERE id = ?
            """,
            (nouveau_nom, repas_id),
        )
        # Stocker le nombre de lignes affectées avant de fermer la connexion
        rows_affected = self.cursor.rowcount
        self.conn.commit()
        self.disconnect()
        return rows_affected > 0

    def get_repas(self, repas_id):
        """Récupère un repas par son ID avec ses informations et aliments"""
        self.connect()

        # Récupérer les informations de base du repas
        self.cursor.execute("SELECT * FROM repas WHERE id = ?", (repas_id,))
        result = self.cursor.fetchone()

        if not result:
            self.disconnect()
            return None

        repas = dict(result)

        # Récupérer les aliments pour ce repas
        self.cursor.execute(
            """
            SELECT ra.quantite, a.* 
            FROM repas_aliments ra
            JOIN aliments a ON ra.aliment_id = a.id
            WHERE ra.repas_id = ?
            """,
            (repas_id,),
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

        self.disconnect()
        return repas
