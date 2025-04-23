import sqlite3
import os
import sys
from pathlib import Path


def main():
    # Déterminer le chemin vers la base de données
    if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
        # Mode exécutable
        app_name = "Health&Food"
        user_data_dir = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), app_name, "data"
        )
        db_path = os.path.join(user_data_dir, "nutrition_sportive.db")
    else:
        # Mode développement
        project_dir = Path(__file__).resolve().parent.parent
        data_dir = os.path.join(project_dir, "data")
        db_path = os.path.join(data_dir, "nutrition_sportive.db")

    print(f"Tentative de mise à jour de la base de données: {db_path}")

    # Vérifier si le fichier existe
    if not os.path.exists(db_path):
        print(
            f"Erreur: Le fichier de base de données n'existe pas à l'emplacement: {db_path}"
        )
        return False

    try:
        # Se connecter à la base de données
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Activer les contraintes de clés étrangères
        cursor.execute("PRAGMA foreign_keys = ON")

        # Vérifier si la table aliments_composes existe déjà
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='aliments_composes'"
        )
        table_exists = cursor.fetchone() is not None

        if table_exists:
            print(
                "La table 'aliments_composes' existe déjà. Aucune modification nécessaire."
            )
            return True

        # Créer les tables nécessaires
        print("Ajout des tables pour les aliments composés...")

        # Table pour les aliments composés
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aliments_composes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                description TEXT,
                categorie TEXT
            )
        """
        )

        # Table pour les ingrédients des aliments composés
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aliments_composes_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aliment_compose_id INTEGER,
                aliment_id INTEGER,
                quantite REAL,
                FOREIGN KEY (aliment_compose_id) REFERENCES aliments_composes (id) ON DELETE CASCADE,
                FOREIGN KEY (aliment_id) REFERENCES aliments (id) ON DELETE CASCADE
            )
        """
        )

        # Valider les modifications
        conn.commit()
        print("Les tables pour les aliments composés ont été ajoutées avec succès!")

        # Fermer la connexion
        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"Erreur SQLite lors de la mise à jour de la base de données: {e}")
        return False
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("Mise à jour de la base de données terminée avec succès.")
    else:
        print("La mise à jour de la base de données a échoué.")

    # Pause pour voir le résultat si exécuté en double-cliquant
    if sys.platform.startswith("win"):
        input("Appuyez sur Entrée pour fermer cette fenêtre...")
