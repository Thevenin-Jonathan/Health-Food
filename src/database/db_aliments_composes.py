import sqlite3
import traceback
from .db_connector import DBConnector


class AlimentsComposesManager(DBConnector):
    def ajouter_aliment_compose(self, nom, description, categorie=None):
        """Ajoute un nouvel aliment composé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                INSERT INTO aliments_composes (nom, description, categorie)
                VALUES (?, ?, ?)
                """,
                (nom, description, categorie),
            )
            aliment_compose_id = self.cursor.lastrowid
            self.conn.commit()
            return aliment_compose_id
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erreur lors de l'ajout de l'aliment composé: {e}")
            return None
        finally:
            self.disconnect()

    def ajouter_ingredient_aliment_compose(
        self, aliment_compose_id, aliment_id, quantite
    ):
        """Ajoute un ingrédient à un aliment composé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                INSERT INTO aliments_composes_ingredients (aliment_compose_id, aliment_id, quantite)
                VALUES (?, ?, ?)
                """,
                (aliment_compose_id, aliment_id, quantite),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erreur lors de l'ajout de l'ingrédient: {e}")
            return False
        finally:
            self.disconnect()

    def supprimer_ingredient_aliment_compose(self, aliment_compose_id, aliment_id):
        """Supprime un ingrédient d'un aliment composé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                DELETE FROM aliments_composes_ingredients
                WHERE aliment_compose_id = ? AND aliment_id = ?
                """,
                (aliment_compose_id, aliment_id),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erreur lors de la suppression de l'ingrédient: {e}")
            return False
        finally:
            self.disconnect()

    def get_aliments_composes(self, categorie=None):
        """Récupère tous les aliments composés, éventuellement filtrés par catégorie"""
        self.connect()
        try:
            if categorie:
                self.cursor.execute(
                    """
                    SELECT * FROM aliments_composes WHERE categorie = ?
                    """,
                    (categorie,),
                )
            else:
                self.cursor.execute("SELECT * FROM aliments_composes")

            aliments_composes = []
            for row in self.cursor.fetchall():
                aliment_compose = dict(row)
                # Ajouter les ingrédients
                aliment_compose["ingredients"] = self.get_ingredients_aliment_compose(
                    aliment_compose["id"]
                )
                # Calculer les valeurs nutritionnelles totales
                totals = self.calculer_valeurs_nutritionnelles_aliment_compose(
                    aliment_compose["id"]
                )
                aliment_compose.update(totals)
                aliments_composes.append(aliment_compose)

            return aliments_composes
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des aliments composés: {e}")
            return []
        finally:
            self.disconnect()

    def get_aliment_compose(self, aliment_compose_id):
        """Récupère un aliment composé spécifique avec tous ses ingrédients"""
        self.connect()
        try:
            self.cursor.execute(
                """
                SELECT * FROM aliments_composes WHERE id = ?
                """,
                (aliment_compose_id,),
            )
            row = self.cursor.fetchone()
            if not row:
                return None

            aliment_compose = dict(row)
            # Ajouter les ingrédients
            aliment_compose["ingredients"] = self.get_ingredients_aliment_compose(
                aliment_compose_id
            )
            # Calculer les valeurs nutritionnelles totales
            totals = self.calculer_valeurs_nutritionnelles_aliment_compose(
                aliment_compose_id
            )
            aliment_compose.update(totals)

            return aliment_compose
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération de l'aliment composé: {e}")
            return None
        finally:
            self.disconnect()

    def get_ingredients_aliment_compose(self, aliment_compose_id):
        """Récupère tous les ingrédients d'un aliment composé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                SELECT aci.aliment_id, aci.quantite, a.nom, 
                      a.calories, a.proteines, a.glucides, a.lipides, a.fibres, a.prix_kg
                FROM aliments_composes_ingredients aci
                JOIN aliments a ON aci.aliment_id = a.id
                WHERE aci.aliment_compose_id = ?
                """,
                (aliment_compose_id,),
            )

            ingredients = []
            for row in self.cursor.fetchall():
                ingredient = dict(row)
                ingredients.append(ingredient)

            return ingredients
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des ingrédients: {e}")
            return []
        finally:
            self.disconnect()

    def calculer_valeurs_nutritionnelles_aliment_compose(self, aliment_compose_id):
        """Calcule les valeurs nutritionnelles totales d'un aliment composé normalisées pour 100g"""
        ingredients = self.get_ingredients_aliment_compose(aliment_compose_id)

        total_calories = 0
        total_proteines = 0
        total_glucides = 0
        total_lipides = 0
        total_fibres = 0
        total_cout = 0

        # Calculer le poids total des ingrédients
        poids_total = sum(ingredient["quantite"] for ingredient in ingredients)

        # Si le poids total est nul, éviter la division par zéro
        if poids_total == 0:
            return {
                "total_calories": 0,
                "total_proteines": 0,
                "total_glucides": 0,
                "total_lipides": 0,
                "total_fibres": 0,
                "total_cout": 0,
            }

        # Facteur de normalisation pour ramener à 100g
        facteur_normalisation = 100.0 / poids_total

        for ingredient in ingredients:
            # Calculer les valeurs pour la quantité spécifiée
            ratio = ingredient["quantite"] / 100.0
            total_calories += ingredient["calories"] * ratio
            total_proteines += ingredient["proteines"] * ratio
            total_glucides += ingredient["glucides"] * ratio
            total_lipides += ingredient["lipides"] * ratio

            if "fibres" in ingredient and ingredient["fibres"]:
                total_fibres += ingredient["fibres"] * ratio

            if "prix_kg" in ingredient and ingredient["prix_kg"]:
                total_cout += (ingredient["prix_kg"] / 1000) * ingredient["quantite"]

        # Normaliser toutes les valeurs nutritionnelles pour 100g
        total_calories *= facteur_normalisation
        total_proteines *= facteur_normalisation
        total_glucides *= facteur_normalisation
        total_lipides *= facteur_normalisation
        total_fibres *= facteur_normalisation

        # Le coût est déjà calculé pour la quantité totale, on le normalise aussi
        total_cout *= facteur_normalisation

        return {
            "total_calories": total_calories,
            "total_proteines": total_proteines,
            "total_glucides": total_glucides,
            "total_lipides": total_lipides,
            "total_fibres": total_fibres,
            "total_cout": total_cout,
        }

    def modifier_aliment_compose(
        self, aliment_compose_id, nom, description, categorie=None
    ):
        """Modifie les informations d'un aliment composé"""
        self.connect()
        try:
            self.cursor.execute(
                """
                UPDATE aliments_composes
                SET nom = ?, description = ?, categorie = ?
                WHERE id = ?
                """,
                (nom, description, categorie, aliment_compose_id),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erreur lors de la modification de l'aliment composé: {e}")
            return False
        finally:
            self.disconnect()

    def supprimer_aliment_compose(self, aliment_compose_id):
        """Supprime un aliment composé et tous ses ingrédients"""
        self.connect()
        try:
            # Les ingrédients seront supprimés automatiquement grâce à ON DELETE CASCADE
            self.cursor.execute(
                """
                DELETE FROM aliments_composes
                WHERE id = ?
                """,
                (aliment_compose_id,),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Erreur lors de la suppression de l'aliment composé: {e}")
            return False
        finally:
            self.disconnect()

    def ajouter_aliment_compose_a_repas(
        self, repas_id, aliment_compose_id, quantite_totale
    ):
        """Ajoute tous les ingrédients d'un aliment composé à un repas
        Cette méthode ajoute chaque ingrédient de l'aliment composé au repas
        en ajustant les quantités proportionnellement à la quantité totale demandée.
        """
        try:
            # Récupérer l'aliment composé avec ses ingrédients
            aliment_compose = self.get_aliment_compose(aliment_compose_id)
            if not aliment_compose:
                return False

            ingredients = aliment_compose.get("ingredients", [])
            if not ingredients:
                return False

            # Calculer le poids total actuel de l'aliment composé (somme des ingrédients)
            poids_total_actuel = sum(
                ingredient["quantite"] for ingredient in ingredients
            )

            if poids_total_actuel == 0:
                return False  # Éviter la division par zéro

            # Facteur d'ajustement pour obtenir la quantité totale souhaitée
            facteur_ajustement = quantite_totale / poids_total_actuel

            # Pour chaque ingrédient, calculer sa nouvelle quantité et l'ajouter au repas
            for ingredient in ingredients:
                nouvelle_quantite = ingredient["quantite"] * facteur_ajustement

                # Ajouter cet ingrédient au repas
                self.connect()
                try:
                    # Vérifier si l'aliment existe déjà dans ce repas
                    self.cursor.execute(
                        """
                        SELECT id FROM repas_aliments 
                        WHERE repas_id = ? AND aliment_id = ?
                        """,
                        (repas_id, ingredient["aliment_id"]),
                    )
                    existing = self.cursor.fetchone()

                    if existing:
                        # Mettre à jour la quantité existante
                        self.cursor.execute(
                            """
                            UPDATE repas_aliments 
                            SET quantite = quantite + ? 
                            WHERE repas_id = ? AND aliment_id = ?
                            """,
                            (nouvelle_quantite, repas_id, ingredient["aliment_id"]),
                        )
                    else:
                        # Ajouter un nouvel ingrédient
                        self.cursor.execute(
                            """
                            INSERT INTO repas_aliments (repas_id, aliment_id, quantite) 
                            VALUES (?, ?, ?)
                            """,
                            (repas_id, ingredient["aliment_id"], nouvelle_quantite),
                        )

                    self.conn.commit()

                finally:
                    self.disconnect()

            return True

        except Exception as e:
            print(f"Erreur lors de l'ajout d'un aliment composé à un repas: {e}")

            traceback.print_exc()
            return False

    def get_categories_aliments_composes(self):
        """Récupère toutes les catégories uniques d'aliments composés"""
        self.connect()
        try:
            self.cursor.execute(
                """
                SELECT DISTINCT categorie FROM aliments_composes
                WHERE categorie IS NOT NULL AND categorie != ''
                """
            )

            categories = [row[0] for row in self.cursor.fetchall()]
            return categories
        except sqlite3.Error as e:
            print(
                f"Erreur lors de la récupération des catégories d'aliments composés: {e}"
            )
            return []
        finally:
            self.disconnect()
