import traceback
import sqlite3
from .db_connector import DBConnector


class CoursesManager(DBConnector):
    """Gestionnaire pour la persistance des états de la liste de courses"""

    def sauvegarder_etats_courses(self, etats_semaine):
        """Sauvegarde les états des cases à cocher pour toutes les semaines

        Args:
            etats_semaine (dict): Dictionnaire avec {semaine_id: {aliment_id: état}}

        Returns:
            bool: True si l'opération a réussi
        """
        # Vérifier si le dictionnaire est vide
        if not etats_semaine:
            return True

        self.connect()
        try:
            # Utiliser une transaction pour s'assurer que tout est sauvegardé ou rien
            self.cursor.execute("BEGIN TRANSACTION")

            # Au lieu de supprimer tous les états, supprimer uniquement ceux des semaines à mettre à jour
            for semaine_key in etats_semaine.keys():
                # Supprimer uniquement les états de la semaine en cours
                self.cursor.execute(
                    "DELETE FROM courses_etat WHERE semaine_id = ?", (semaine_key,)
                )

            # Insérer les nouveaux états
            values = []  # Pour l'insertion par lots (plus efficace)
            for semaine_key, aliments in etats_semaine.items():
                for aliment_id, state in aliments.items():
                    # Vérifier que state est bien un entier
                    if not isinstance(state, int):
                        try:
                            state = int(state)
                        except ValueError:
                            # Fallback à Qt.Checked (2) par défaut
                            state = 2

                    values.append((semaine_key, aliment_id, state))

            # Utiliser executemany pour une insertion plus efficace
            if values:
                self.cursor.executemany(
                    """
                    INSERT INTO courses_etat (semaine_id, aliment_id, checked) 
                    VALUES (?, ?, ?)
                    """,
                    values,
                )

            self.conn.commit()
            return True
        except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
            self.conn.rollback()
            print(f"Erreur lors de la sauvegarde des états des courses: {e}")

            traceback.print_exc()
            return False
        finally:
            self.disconnect()

    def charger_etats_courses(self):
        """Charge tous les états des cases à cocher depuis la base de données

        Returns:
            dict: Dictionnaire avec {semaine_id: {aliment_id: état}}
        """
        self.connect()
        try:
            etats = {}
            self.cursor.execute(
                "SELECT semaine_id, aliment_id, checked FROM courses_etat"
            )
            rows = self.cursor.fetchall()

            for row in rows:
                semaine_key, aliment_id, checked = row

                if semaine_key not in etats:
                    etats[semaine_key] = {}

                etats[semaine_key][aliment_id] = checked
            return etats
        except sqlite3.DatabaseError as e:
            print(f"Erreur lors du chargement des états des courses: {e}")
            traceback.print_exc()
            return {}
        finally:
            self.disconnect()
