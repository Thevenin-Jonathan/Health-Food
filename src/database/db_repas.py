from .db_connector import DBConnector
from .db_repas_types import RepasTypesManager


class RepasManager(DBConnector):
    """Gestion des repas dans la base de données"""

    def ajouter_repas(self, nom, jour, ordre, semaine_id=None, repas_type_id=None):
        """Ajoute un nouveau repas avec option de numéro de semaine"""
        self.connect()
        self.cursor.execute(
            """
        INSERT INTO repas (nom, jour, ordre, semaine_id, repas_type_id)
        VALUES (?, ?, ?, ?, ?)
        """,
            (nom, jour, ordre, semaine_id, repas_type_id),
        )

        repas_id = self.cursor.lastrowid
        self.conn.commit()
        self.disconnect()
        return repas_id

    def ajouter_aliment_repas(self, repas_id, aliment_id, quantite, est_modifie=False):
        """Ajoute un aliment à un repas avec sa quantité"""
        self.connect()
        try:
            # Vérifier si l'aliment existe déjà dans ce repas
            self.cursor.execute(
                """
                SELECT id FROM repas_aliments 
                WHERE repas_id = ? AND aliment_id = ?
                """,
                (repas_id, aliment_id),
            )
            existing = self.cursor.fetchone()

            if existing:
                # Mise à jour de la quantité
                self.cursor.execute(
                    """
                    UPDATE repas_aliments 
                    SET quantite = ?, est_modifie = ? 
                    WHERE repas_id = ? AND aliment_id = ?
                    """,
                    (quantite, 1 if est_modifie else 0, repas_id, aliment_id),
                )
            else:
                # Ajout d'un nouvel aliment
                self.cursor.execute(
                    """
                    INSERT INTO repas_aliments (repas_id, aliment_id, quantite, est_modifie) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (repas_id, aliment_id, quantite, 1 if est_modifie else 0),
                )

            last_id = self.cursor.lastrowid
            self.conn.commit()
            self.disconnect()
            return last_id
        except Exception as e:
            print(
                f"Erreur lors de l'ajout de l'aliment {aliment_id} au repas {repas_id}: {e}"
            )
            self.conn.rollback()
            self.disconnect()
            return 0

    def modifier_quantite_aliment_repas(self, repas_id, aliment_id, nouvelle_quantite):
        """Modifie la quantité d'un aliment dans un repas et marque comme personnalisé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                UPDATE repas_aliments 
                SET quantite = ?, est_modifie = 1
                WHERE repas_id = ? AND aliment_id = ?
                """,
                (nouvelle_quantite, repas_id, aliment_id),
            )
            self.conn.commit()
            rows_affected = self.cursor.rowcount > 0
            self.disconnect()
            return rows_affected
        except Exception as e:
            print(f"Erreur lors de la modification de la quantité: {e}")
            self.conn.rollback()
            self.disconnect()
            return False

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
                SELECT id, nom, jour, ordre, repas_type_id FROM repas 
                WHERE semaine_id = ? 
                ORDER BY jour, ordre
                """,
                (semaine_id,),
            )
        else:
            # Récupérer les repas sans numéro de semaine (comportement historique)
            self.cursor.execute(
                """
                SELECT id, nom, jour, ordre, repas_type_id FROM repas 
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
            repas["total_cout"] = sum(
                (a.get("prix_kg", 0) / 1000) * a["quantite"] for a in aliments
            )

            result[repas["jour"]].append(repas)

        # Modifier le tri pour garantir le bon ordre
        for jour in jours:
            # Trier les repas explicitement par ordre
            result[jour] = sorted(result[jour], key=lambda repas: repas["ordre"])

        self.disconnect()
        return result

    def decaler_ordres(self, jour, semaine_id, ordre_insertion):
        """
        Décale les ordres des repas pour faire de la place à un nouveau repas

        Args:
            jour: Le jour concerné
            semaine_id: ID de la semaine
            ordre_insertion: L'ordre où le nouveau repas sera inséré

        Cette méthode augmente de 1 l'ordre de tous les repas dont l'ordre est >= ordre_insertion
        """
        self.connect()
        self.cursor.execute(
            """
            UPDATE repas 
            SET ordre = ordre + 1
            WHERE jour = ? AND semaine_id = ? AND ordre >= ?
            """,
            (jour, semaine_id, ordre_insertion),
        )
        self.conn.commit()
        self.disconnect()

    def normaliser_ordres(self, jour, semaine_id):
        """Réindexe les ordres pour qu'ils soient des entiers consécutifs (1, 2, 3...)"""
        self.connect()

        # Récupérer tous les repas du jour, triés par ordre
        self.cursor.execute(
            """
            SELECT id, ordre FROM repas 
            WHERE jour = ? AND semaine_id = ?
            ORDER BY ordre
            """,
            (jour, semaine_id),
        )

        repas_list = self.cursor.fetchall()

        # Mettre à jour les ordres pour qu'ils soient consécutifs
        for i, repas in enumerate(repas_list):
            repas_id = repas[0]
            nouvel_ordre = i + 1  # Commencer à 1

            # Mettre à jour l'ordre seulement s'il est différent
            if repas[1] != nouvel_ordre:
                self.cursor.execute(
                    """
                    UPDATE repas SET ordre = ? WHERE id = ?
                    """,
                    (nouvel_ordre, repas_id),
                )

        self.conn.commit()
        self.disconnect()

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

    def update_repas_based_on_recipe(self, repas_type_id):
        """Met à jour tous les repas basés sur la recette spécifiée"""
        self.connect()

        repas_types_manager = RepasTypesManager(self.db_file)
        recette = repas_types_manager.get_repas_type(repas_type_id)

        self.cursor.execute(
            """
            SELECT id, nom, jour, ordre, semaine_id
            FROM repas
            WHERE repas_type_id = ?
            """,
            (repas_type_id,),
        )

        repas_list = [dict(row) for row in self.cursor.fetchall()]

        for repas in repas_list:
            repas_id = repas["id"]

            # Supprimer tous les ingrédients existants
            self.cursor.execute(
                "DELETE FROM repas_aliments WHERE repas_id = ?", (repas_id,)
            )

            # Ajouter les ingrédients de la recette mise à jour
            for aliment in recette["aliments"]:
                self.cursor.execute(
                    """
                    INSERT INTO repas_aliments (repas_id, aliment_id, quantite)
                    VALUES (?, ?, ?)
                    """,
                    (repas_id, aliment["id"], aliment["quantite"]),
                )

        self.conn.commit()
        self.disconnect()

        # Retourner le nombre de repas mis à jour
        return len(repas_list)

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
        try:
            # Lancer une transaction pour optimiser les performances
            self.cursor.execute("BEGIN TRANSACTION")

            # Obtenir le jour et l'ordre actuels du repas
            self.cursor.execute(
                "SELECT jour, ordre FROM repas WHERE id = ?", (repas_id,)
            )
            result = self.cursor.fetchone()

            if not result:
                self.conn.rollback()
                self.disconnect()
                return False

            jour_origine = result["jour"]
            ordre_origine = result["ordre"]

            # Mettre à jour le repas
            self.cursor.execute(
                """
                UPDATE repas
                SET jour = ?, ordre = ?
                WHERE id = ?
                """,
                (nouveau_jour, nouvel_ordre, repas_id),
            )

            # Réorganiser les ordres dans le jour d'origine
            if jour_origine != nouveau_jour:
                self.cursor.execute(
                    """
                    UPDATE repas
                    SET ordre = ordre - 1
                    WHERE jour = ? AND ordre > ?
                    """,
                    (jour_origine, ordre_origine),
                )

            # Valider la transaction
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Erreur lors du changement de jour du repas {repas_id}: {e}")
            self.conn.rollback()
            return False

        finally:
            self.disconnect()

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

    def sauvegarder_nom_semaine(self, semaine_id, nom_personnalise):
        """Sauvegarde le nom personnalisé d'une semaine"""
        self.connect()

        # Vérifier si la semaine existe déjà
        self.cursor.execute("SELECT id FROM semaines WHERE id = ?", (semaine_id,))
        exists = self.cursor.fetchone()

        if exists:
            # Mettre à jour le nom existant
            self.cursor.execute(
                "UPDATE semaines SET nom_personnalise = ? WHERE id = ?",
                (nom_personnalise, semaine_id),
            )
        else:
            # Insérer un nouveau nom
            self.cursor.execute(
                "INSERT INTO semaines (id, nom_personnalise) VALUES (?, ?)",
                (semaine_id, nom_personnalise),
            )

        self.conn.commit()
        self.disconnect()
        return True

    def get_noms_semaines(self):
        """Récupère tous les noms personnalisés des semaines"""
        self.connect()
        self.cursor.execute("SELECT id, nom_personnalise FROM semaines")
        result = {row[0]: row[1] for row in self.cursor.fetchall()}
        self.disconnect()
        return result

    def supprimer_nom_semaine(self, semaine_id):
        """Supprime le nom personnalisé d'une semaine"""
        self.connect()
        self.cursor.execute("DELETE FROM semaines WHERE id = ?", (semaine_id,))
        self.conn.commit()
        self.disconnect()
