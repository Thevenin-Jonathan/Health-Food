import sqlite3
import os
import sys
import shutil


class DBConnector:
    """Classe de base pour la gestion des connexions à la base de données (Singleton)"""

    # Variable de classe pour stocker l'instance unique
    _instance = None
    _db_path_logged = False  # Pour éviter de répéter le message de chemin DB

    def __new__(cls, db_file="nutrition_sportive.db"):
        # Si aucune instance n'existe, en créer une
        if cls._instance is None:
            cls._instance = super(DBConnector, cls).__new__(cls)
            # Initialiser l'instance (ceci n'est appelé qu'une seule fois)
            cls._instance._initialize(db_file)
        return cls._instance

    def _initialize(self, db_file):
        """Initialisation réelle de l'instance (appelée une seule fois)"""
        # Nom de l'application pour créer un dossier dédié
        app_name = "Health&Food"

        # Déterminer si on est dans un environnement PyInstaller ou en développement
        if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
            # En mode exécutable (PyInstaller)
            # Dossier d'installation (lecture seule)
            install_dir = os.path.dirname(sys.executable)
            install_data_dir = os.path.join(install_dir, "data")

            # Dossier de données utilisateur dans AppData (pour l'écriture)
            user_data_dir = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")), app_name, "data"
            )

            # S'assurer que le dossier de données utilisateur existe
            os.makedirs(user_data_dir, exist_ok=True)

            # Chemin vers le fichier de base de données dans le dossier utilisateur
            user_db_path = os.path.join(user_data_dir, db_file)

            # Vérifier si la base de données existe déjà dans le dossier utilisateur
            if not os.path.exists(user_db_path):
                # Si elle n'existe pas, essayer de la copier depuis le dossier d'installation
                install_db_path = os.path.join(install_data_dir, db_file)
                if os.path.exists(install_db_path):
                    try:
                        print(
                            f"Copie de la base de données depuis {install_db_path} vers {user_db_path}"
                        )
                        shutil.copy2(install_db_path, user_db_path)
                        print("Base de données copiée avec succès.")
                    except Exception as e:
                        print(f"Erreur lors de la copie de la base de données: {e}")

            # Utiliser le chemin dans le dossier utilisateur pour la base de données
            self.db_file = user_db_path
        else:
            # En mode développement, utiliser le même comportement qu'avant
            project_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../..")
            )
            data_dir = os.path.join(project_dir, "data")

            # S'assurer que le dossier data existe
            os.makedirs(data_dir, exist_ok=True)

            # Chemin absolu vers le fichier de la base de données
            self.db_file = os.path.join(data_dir, db_file)

        # Afficher le chemin une seule fois
        if not DBConnector._db_path_logged:
            print(f"Utilisation de la base de données: {self.db_file}")
            DBConnector._db_path_logged = True

        self.conn = None
        self.cursor = None

    def __init__(self, db_file="nutrition_sportive.db"):
        # L'initialisation réelle est faite dans __new__, cette méthode ne fait rien
        pass

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

    def get_db_version(self):
        """Obtient la version actuelle de la base de données"""
        self.connect()
        try:
            self.cursor.execute("PRAGMA user_version")
            version = self.cursor.fetchone()[0]
            return version
        except Exception as e:
            print(f"Erreur lors de la récupération de la version de la DB: {e}")
            return 0
        finally:
            self.disconnect()

    def set_db_version(self, version):
        """Définit la version de la base de données"""
        self.connect()
        try:
            self.cursor.execute(f"PRAGMA user_version = {version}")
            self.conn.commit()
        except Exception as e:
            print(f"Erreur lors de la définition de la version de la DB: {e}")
        finally:
            self.disconnect()

    def init_db(self):
        """Initialise la structure de la base de données"""
        # Vérifier la version actuelle et appliquer les migrations si nécessaire
        current_version = self.get_db_version()
        print(f"Version actuelle de la base de données: {current_version}")

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
            objectif_lipides INTEGER,
            theme_actif TEXT DEFAULT 'Vert Nature'
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
            est_modifie INTEGER DEFAULT 0,
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

        # Table pour les états des cases à cocher de la liste de courses
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses_etat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semaine_id TEXT,
                aliment_id TEXT,
                checked INTEGER,
                UNIQUE(semaine_id, aliment_id)
            )
            """
        )

        # Table pour stocker les multiplicateurs de repas pour la liste de courses
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repas_multiplicateurs (
                repas_id INTEGER PRIMARY KEY,
                multiplicateur INTEGER DEFAULT 1,
                ignore_course BOOLEAN DEFAULT 0,
                FOREIGN KEY (repas_id) REFERENCES repas (id) ON DELETE CASCADE
            )
            """
        )

        # Si c'est une nouvelle base de données, définir la version à 1
        if current_version == 0:
            self.cursor.execute("PRAGMA user_version = 1")
            print("Base de données initialisée à la version 1")

        self.conn.commit()
        self.disconnect()
