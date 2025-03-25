from .db_connector import DBConnector


class ExportImportManager(DBConnector):
    """Gestionnaire d'import/export pour la base de données"""

    def __init__(self, db_file="nutrition_sportive.db", db_manager=None):
        """Initialise le gestionnaire d'export/import"""
        super().__init__(db_file)
        self.db_manager = (
            db_manager  # Référence au gestionnaire principal pour accéder aux méthodes
        )

    def exporter_aliments(self):
        """Exporte tous les aliments de la base de données"""
        self.connect()
        self.cursor.execute("SELECT * FROM aliments")
        aliments = [dict(row) for row in self.cursor.fetchall()]
        self.disconnect()
        return aliments

    def exporter_repas_types(self):
        """Exporte tous les repas types avec leurs aliments"""
        repas_types = []

        # Obtenir tous les repas types
        self.connect()
        self.cursor.execute("SELECT * FROM repas_types")
        types = [dict(row) for row in self.cursor.fetchall()]

        # Pour chaque repas type, récupérer ses aliments
        for repas_type in types:
            self.cursor.execute(
                """
                SELECT a.id, a.nom, a.marque, a.categorie, rta.quantite
                FROM repas_types_aliments rta
                JOIN aliments a ON rta.aliment_id = a.id
                WHERE rta.repas_type_id = ?
                """,
                (repas_type["id"],),
            )
            aliments = [
                {
                    "id": row["id"],
                    "nom": row["nom"],
                    "marque": row["marque"],
                    "categorie": row["categorie"],
                    "quantite": row["quantite"],
                }
                for row in self.cursor.fetchall()
            ]

            repas_type["aliments"] = aliments
            repas_types.append(repas_type)

        self.disconnect()
        return repas_types

    def exporter_planning(self, semaine_id=None):
        """Exporte les repas d'une semaine spécifique ou de la semaine courante"""
        self.connect()

        # Si aucun ID de semaine n'est fourni, récupérer le plus récent
        if semaine_id is None:
            self.cursor.execute("SELECT MAX(semaine_id) FROM repas")
            result = self.cursor.fetchone()
            semaine_id = result[0] if result and result[0] else 1

        # Récupérer tous les repas de cette semaine
        planning = {}

        self.cursor.execute(
            "SELECT * FROM repas WHERE semaine_id = ? ORDER BY jour, ordre",
            (semaine_id,),
        )
        repas_list = [dict(row) for row in self.cursor.fetchall()]

        # Organiser par jour
        for repas in repas_list:
            jour = repas["jour"]
            if jour not in planning:
                planning[jour] = []

            # Récupérer les aliments de ce repas
            self.cursor.execute(
                """
                SELECT a.id, a.nom, a.marque, a.categorie, ra.quantite
                FROM repas_aliments ra
                JOIN aliments a ON ra.aliment_id = a.id
                WHERE ra.repas_id = ?
                """,
                (repas["id"],),
            )

            aliments = [
                {
                    "id": row["id"],
                    "nom": row["nom"],
                    "marque": row["marque"],
                    "categorie": row["categorie"],
                    "quantite": row["quantite"],
                }
                for row in self.cursor.fetchall()
            ]

            repas["aliments"] = aliments
            planning[jour].append(repas)

        self.disconnect()
        return planning

    def importer_aliments(self, aliments_data):
        """Importe des aliments depuis un dictionnaire"""
        count = 0
        for aliment in aliments_data:
            try:
                # Vérifier si l'aliment existe déjà par nom et marque
                self.connect()
                self.cursor.execute(
                    "SELECT id FROM aliments WHERE nom = ? AND marque = ?",
                    (aliment["nom"], aliment.get("marque", "")),
                )
                existing = self.cursor.fetchone()

                if existing:
                    # Mise à jour de l'aliment existant
                    aliment_id = existing[0]
                    self.db_manager.modifier_aliment(aliment_id, aliment)
                else:
                    # Ajout d'un nouvel aliment
                    self.db_manager.ajouter_aliment(aliment)
                count += 1
            except Exception as e:
                print(
                    f"Erreur lors de l'importation de l'aliment {aliment.get('nom', 'inconnu')}: {e}"
                )
            finally:
                self.disconnect()

        return count

    def importer_repas_types(self, repas_types_data):
        """Importe des repas types depuis un dictionnaire"""
        count = 0
        for repas_type in repas_types_data:
            try:
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
                    self.db_manager.modifier_repas_type(
                        repas_type_id,
                        repas_type["nom"],
                        repas_type.get("description", ""),
                    )

                    # Supprimer les aliments existants
                    for aliment in self.db_manager.get_repas_type(repas_type_id)[
                        "aliments"
                    ]:
                        self.db_manager.supprimer_aliment_repas_type(
                            repas_type_id, aliment["id"]
                        )
                else:
                    # Ajout d'un nouveau repas type
                    repas_type_id = self.db_manager.ajouter_repas_type(
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
                        self.db_manager.ajouter_aliment_repas_type(
                            repas_type_id, aliment_id, aliment["quantite"]
                        )
                count += 1
            except Exception as e:
                print(
                    f"Erreur lors de l'importation du repas type {repas_type.get('nom', 'inconnu')}: {e}"
                )

        return count

    def importer_planning(self, planning_data, semaine_id=None):
        """Importe un planning hebdomadaire"""
        try:
            if semaine_id is None:
                # Utiliser l'ID de semaine actuel ou en créer un nouveau
                semaines = self.db_manager.get_semaines_existantes()
                semaine_id = max(semaines) + 1 if semaines else 1

            count = 0
            for jour, repas_list in planning_data.items():
                for repas in repas_list:
                    # Créer un nouveau repas
                    repas_id = self.db_manager.ajouter_repas(
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
                            self.db_manager.ajouter_aliment_repas(
                                repas_id, aliment_id, aliment["quantite"]
                            )
                    count += 1

            return count
        except Exception as e:
            print(f"Erreur lors de l'importation du planning: {e}")
            return 0
