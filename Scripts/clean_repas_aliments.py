#!/usr/bin/env python
"""
Script pour effacer le contenu de la table repas_aliments dans la base de données.
"""

import sqlite3
import os
import sys


def effacer_table_repas_aliments(confirmation=True):
    """
    Efface le contenu de la table repas_aliments.

    Args:
        confirmation (bool): Si True, demande une confirmation à l'utilisateur

    Returns:
        bool: True si l'opération a réussi, False sinon
    """
    # Chemin de la base de données
    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "nutrition_sportive.db"
    )

    # Vérifier si la base de données existe
    if not os.path.exists(db_path):
        print(f"Erreur: La base de données n'existe pas à l'emplacement {db_path}")
        return False

    if confirmation:
        response = input(
            "Voulez-vous vraiment effacer tous les enregistrements de la table repas_aliments? (o/n): "
        )
        if response.lower() != "o":
            print("Opération annulée.")
            return False

    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier si la table existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='repas_aliments'"
        )
        if not cursor.fetchone():
            print(
                "Erreur: La table repas_aliments n'existe pas dans la base de données."
            )
            conn.close()
            return False

        # Supprimer le contenu de la table
        cursor.execute("DELETE FROM repas_aliments")

        # Enregistrer les modifications
        conn.commit()

        # Nombre de lignes supprimées
        rows_deleted = cursor.rowcount
        print(
            f"Succès: {rows_deleted} enregistrements ont été supprimés de la table repas_aliments."
        )

        # Fermer la connexion
        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
        return False
    except FileNotFoundError as e:
        print(f"Fichier introuvable: {e}")
        return False
    except PermissionError as e:
        print(f"Erreur de permission: {e}")
        return False


if __name__ == "__main__":
    # Si des arguments sont passés, vérifier s'il y a une option pour sauter la confirmation
    skip_confirmation = "-y" in sys.argv or "--yes" in sys.argv

    # Exécuter la fonction
    effacer_table_repas_aliments(not skip_confirmation)
