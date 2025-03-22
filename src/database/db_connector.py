import sqlite3
import os


class DBConnector:
    """Classe de base pour la gestion des connexions à la base de données"""

    def __init__(self, db_file="nutrition_sportive.db"):
        # Calculer le chemin absolu vers le répertoire de projet
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

        # S'assurer que le dossier data existe
        data_dir = os.path.join(project_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Chemin absolu vers le fichier de la base de données
        self.db_file = os.path.join(data_dir, db_file)

        self.conn = None
        self.cursor = None

    def connect(self):
        """Établit une connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            # Activer les contraintes de clés étrangères à chaque connexion
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Erreur de connexion à la base de données: {e}")
            print(f"Chemin de la base de données: {self.db_file}")
            raise

    def disconnect(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def init_db(self):
        """Initialise la structure de la base de données"""
        self.connect()

        # Activer les contraintes de clés étrangères (important pour les suppressions en cascade)
        self.cursor.execute("PRAGMA foreign_keys = ON")

        # Table des semaines
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS semaines (
                id INTEGER PRIMARY KEY,
                nom_personnalise TEXT
            )
            """
        )

        # Table des utilisateurs
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS utilisateur (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            sexe TEXT,
            age INTEGER,
            taille REAL,
            poids REAL,
            niveau_activite TEXT,
            objectif TEXT,
            taux_variation REAL,
            calories_personnalisees INTEGER,        
            regime_alimentaire TEXT DEFAULT 'Régime équilibré',
            proteines_g_kg REAL,
            glucides_g_kg REAL,
            lipides_g_kg REAL,
            objectif_calories INTEGER,
            objectif_proteines INTEGER,
            objectif_glucides INTEGER,
            objectif_lipides INTEGER
        )
        """
        )

        # Table des aliments
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            marque TEXT,
            magasin TEXT,
            categorie TEXT,
            calories REAL,
            proteines REAL,
            glucides REAL,
            lipides REAL,
            fibres REAL,
            prix_kg REAL
        )
        """
        )

        # Table des repas
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repas (
                id INTEGER PRIMARY KEY,
                nom TEXT NOT NULL,
                jour TEXT NOT NULL,
                ordre INTEGER DEFAULT 1,
                semaine_id INTEGER,
                repas_type_id INTEGER
            )
            """
        )

        # Table des aliments dans les repas
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repas_id INTEGER,
            aliment_id INTEGER,
            quantite REAL,
            FOREIGN KEY (repas_id) REFERENCES repas (id) ON DELETE CASCADE,
            FOREIGN KEY (aliment_id) REFERENCES aliments (id) ON DELETE CASCADE
        )
        """
        )

        # Table des repas types
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT
        )
        """
        )

        # Table des aliments dans les repas types
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS repas_types_aliments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repas_type_id INTEGER,
            aliment_id INTEGER,
            quantite REAL,
            FOREIGN KEY (repas_type_id) REFERENCES repas_types (id) ON DELETE CASCADE,
            FOREIGN KEY (aliment_id) REFERENCES aliments (id) ON DELETE CASCADE
        )
        """
        )

        self.conn.commit()
        self.disconnect()
