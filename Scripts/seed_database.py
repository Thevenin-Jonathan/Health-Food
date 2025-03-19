import os
import sys
from src.database.db_manager import DatabaseManager

# Ajouter le chemin parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_database():
    """
    Ajoute des données de test dans la base de données :
    - Aliments avec valeurs nutritionnelles
    - Repas types (recettes)
    - Un profil utilisateur par défaut
    """
    print("Initialisation de la base de données avec des données de test...")

    # Initialiser la base de données
    db = DatabaseManager()
    db.init_db()

    # Données utilisateur par défaut
    user_data = {
        "nom": "Utilisateur Test",
        "sexe": "Homme",
        "age": 36,
        "taille": 172,
        "poids": 73.8,
        "niveau_activite": "Modéré",
        "objectif": "Perte de poids",
        "taux_variation": 8,  # 500g par semaine
        "calories_personnalisees": 0,
        "regime_alimentaire": "Régime hyperprotéiné",
        "proteines_g_kg": 1.8,
        "glucides_g_kg": 2.0,
        "lipides_g_kg": 0.8,
        "objectif_calories": 1659,
        "objectif_proteines": 133,
        "objectif_glucides": 148,
        "objectif_lipides": 59,
    }
    db.sauvegarder_utilisateur(user_data)
    print("✓ Profil utilisateur ajouté")

    # ----------------------
    # Ajouter des aliments
    # ----------------------

    # Catégorie: Protéines
    aliments_proteines = [
        {
            "nom": "Poulet (blanc)",
            "marque": "",
            "magasin": "Carrefour",
            "categorie": "Protéines",
            "calories": 165,
            "proteines": 31,
            "glucides": 0,
            "lipides": 3.6,
            "fibres": 0,
            "prix_kg": 9.90,
        },
        {
            "nom": "Thon en conserve (au naturel)",
            "marque": "Petit Navire",
            "magasin": "Intermarché",
            "categorie": "Protéines",
            "calories": 103,
            "proteines": 24,
            "glucides": 0,
            "lipides": 1,
            "fibres": 0,
            "prix_kg": 15.50,
        },
        {
            "nom": "Oeufs (L)",
            "marque": "",
            "magasin": "Leclerc",
            "categorie": "Protéines",
            "calories": 143,
            "proteines": 12.5,
            "glucides": 0.7,
            "lipides": 9.5,
            "fibres": 0,
            "prix_kg": 6.90,
        },
        {
            "nom": "Steak haché 5%",
            "marque": "Charal",
            "magasin": "Auchan",
            "categorie": "Protéines",
            "calories": 122,
            "proteines": 21,
            "glucides": 0,
            "lipides": 5,
            "fibres": 0,
            "prix_kg": 13.50,
        },
        {
            "nom": "Filet de saumon",
            "marque": "",
            "magasin": "Poissonnerie",
            "categorie": "Protéines",
            "calories": 208,
            "proteines": 20,
            "glucides": 0,
            "lipides": 13,
            "fibres": 0,
            "prix_kg": 19.90,
        },
    ]

    # Catégorie: Féculents
    aliments_feculents = [
        {
            "nom": "Riz blanc",
            "marque": "Taureau Ailé",
            "magasin": "Carrefour",
            "categorie": "Féculents",
            "calories": 356,
            "proteines": 7,
            "glucides": 79,
            "lipides": 0.5,
            "fibres": 1.4,
            "prix_kg": 2.50,
        },
        {
            "nom": "Pâtes complètes",
            "marque": "Panzani",
            "magasin": "Intermarché",
            "categorie": "Féculents",
            "calories": 348,
            "proteines": 12,
            "glucides": 65,
            "lipides": 2.5,
            "fibres": 8.5,
            "prix_kg": 3.20,
        },
        {
            "nom": "Pommes de terre",
            "marque": "",
            "magasin": "Leclerc",
            "categorie": "Féculents",
            "calories": 87,
            "proteines": 2.2,
            "glucides": 19,
            "lipides": 0.1,
            "fibres": 2,
            "prix_kg": 1.50,
        },
        {
            "nom": "Quinoa",
            "marque": "Céréal Bio",
            "magasin": "Biocoop",
            "categorie": "Féculents",
            "calories": 368,
            "proteines": 14,
            "glucides": 64,
            "lipides": 6,
            "fibres": 7,
            "prix_kg": 8.90,
        },
        {
            "nom": "Patate douce",
            "marque": "",
            "magasin": "Auchan",
            "categorie": "Féculents",
            "calories": 86,
            "proteines": 1.6,
            "glucides": 20,
            "lipides": 0.1,
            "fibres": 3,
            "prix_kg": 2.80,
        },
    ]

    # Catégorie: Légumes
    aliments_legumes = [
        {
            "nom": "Brocoli",
            "marque": "",
            "magasin": "Carrefour",
            "categorie": "Légumes",
            "calories": 34,
            "proteines": 2.8,
            "glucides": 7,
            "lipides": 0.4,
            "fibres": 2.6,
            "prix_kg": 2.50,
        },
        {
            "nom": "Épinards",
            "marque": "",
            "magasin": "Marché local",
            "categorie": "Légumes",
            "calories": 23,
            "proteines": 2.9,
            "glucides": 3.6,
            "lipides": 0.4,
            "fibres": 2.2,
            "prix_kg": 3.80,
        },
        {
            "nom": "Carottes",
            "marque": "",
            "magasin": "Leclerc",
            "categorie": "Légumes",
            "calories": 41,
            "proteines": 0.9,
            "glucides": 10,
            "lipides": 0.2,
            "fibres": 2.8,
            "prix_kg": 1.20,
        },
        {
            "nom": "Courgette",
            "marque": "",
            "magasin": "Marché local",
            "categorie": "Légumes",
            "calories": 17,
            "proteines": 1.2,
            "glucides": 3.1,
            "lipides": 0.3,
            "fibres": 1,
            "prix_kg": 1.90,
        },
        {
            "nom": "Poivron rouge",
            "marque": "",
            "magasin": "Auchan",
            "categorie": "Légumes",
            "calories": 31,
            "proteines": 1,
            "glucides": 6,
            "lipides": 0.3,
            "fibres": 2.1,
            "prix_kg": 3.50,
        },
    ]

    # Catégorie: Fruits
    aliments_fruits = [
        {
            "nom": "Banane",
            "marque": "",
            "magasin": "Carrefour",
            "categorie": "Fruits",
            "calories": 89,
            "proteines": 1.1,
            "glucides": 23,
            "lipides": 0.3,
            "fibres": 2.6,
            "prix_kg": 2.20,
        },
        {
            "nom": "Pomme",
            "marque": "",
            "magasin": "Marché local",
            "categorie": "Fruits",
            "calories": 52,
            "proteines": 0.3,
            "glucides": 14,
            "lipides": 0.2,
            "fibres": 2.4,
            "prix_kg": 2.50,
        },
        {
            "nom": "Myrtilles",
            "marque": "",
            "magasin": "Grand Frais",
            "categorie": "Fruits",
            "calories": 57,
            "proteines": 0.7,
            "glucides": 14,
            "lipides": 0.3,
            "fibres": 2.4,
            "prix_kg": 15.90,
        },
        {
            "nom": "Fraises",
            "marque": "",
            "magasin": "Marché local",
            "categorie": "Fruits",
            "calories": 32,
            "proteines": 0.7,
            "glucides": 7.7,
            "lipides": 0.3,
            "fibres": 2,
            "prix_kg": 5.90,
        },
        {
            "nom": "Ananas",
            "marque": "",
            "magasin": "Carrefour",
            "categorie": "Fruits",
            "calories": 50,
            "proteines": 0.5,
            "glucides": 13,
            "lipides": 0.1,
            "fibres": 1.4,
            "prix_kg": 3.50,
        },
    ]

    # Catégorie: Produits laitiers
    aliments_laitiers = [
        {
            "nom": "Yaourt grec",
            "marque": "Fage",
            "magasin": "Carrefour",
            "categorie": "Produits laitiers",
            "calories": 97,
            "proteines": 9,
            "glucides": 3.8,
            "lipides": 5,
            "fibres": 0,
            "prix_kg": 7.90,
        },
        {
            "nom": "Fromage blanc 0%",
            "marque": "Danone",
            "magasin": "Intermarché",
            "categorie": "Produits laitiers",
            "calories": 54,
            "proteines": 8,
            "glucides": 4,
            "lipides": 0.1,
            "fibres": 0,
            "prix_kg": 3.20,
        },
        {
            "nom": "Lait écrémé",
            "marque": "Lactel",
            "magasin": "Leclerc",
            "categorie": "Produits laitiers",
            "calories": 33,
            "proteines": 3.3,
            "glucides": 5,
            "lipides": 0.1,
            "fibres": 0,
            "prix_kg": 1.10,
        },
        {
            "nom": "Skyr",
            "marque": "Arla",
            "magasin": "Carrefour",
            "categorie": "Produits laitiers",
            "calories": 63,
            "proteines": 11,
            "glucides": 4,
            "lipides": 0.2,
            "fibres": 0,
            "prix_kg": 8.50,
        },
        {
            "nom": "Cottage cheese",
            "marque": "St Hubert",
            "magasin": "Monoprix",
            "categorie": "Produits laitiers",
            "calories": 98,
            "proteines": 11.5,
            "glucides": 2.4,
            "lipides": 4.3,
            "fibres": 0,
            "prix_kg": 12.80,
        },
    ]

    # Catégorie: Noix & graines
    aliments_noix = [
        {
            "nom": "Amandes",
            "marque": "",
            "magasin": "Biocoop",
            "categorie": "Noix & graines",
            "calories": 578,
            "proteines": 21,
            "glucides": 22,
            "lipides": 49,
            "fibres": 12.5,
            "prix_kg": 19.90,
        },
        {
            "nom": "Graines de chia",
            "marque": "Naturalia",
            "magasin": "Biocoop",
            "categorie": "Noix & graines",
            "calories": 486,
            "proteines": 17,
            "glucides": 42,
            "lipides": 31,
            "fibres": 34,
            "prix_kg": 16.50,
        },
        {
            "nom": "Noix de cajou",
            "marque": "",
            "magasin": "Carrefour",
            "categorie": "Noix & graines",
            "calories": 553,
            "proteines": 18,
            "glucides": 30,
            "lipides": 44,
            "fibres": 3.3,
            "prix_kg": 18.90,
        },
        {
            "nom": "Beurre de cacahuète",
            "marque": "Jean Hervé",
            "magasin": "Biocoop",
            "categorie": "Noix & graines",
            "calories": 589,
            "proteines": 24,
            "glucides": 20,
            "lipides": 50,
            "fibres": 8,
            "prix_kg": 25.50,
        },
        {
            "nom": "Graines de tournesol",
            "marque": "",
            "magasin": "Naturalia",
            "categorie": "Noix & graines",
            "calories": 585,
            "proteines": 21,
            "glucides": 20,
            "lipides": 51,
            "fibres": 8.6,
            "prix_kg": 9.90,
        },
    ]

    # Catégorie: Suppléments
    aliments_supplements = [
        {
            "nom": "Whey protéine",
            "marque": "MyProtein",
            "magasin": "En ligne",
            "categorie": "Suppléments",
            "calories": 412,
            "proteines": 82,
            "glucides": 7.5,
            "lipides": 7.5,
            "fibres": 0,
            "prix_kg": 30,
        },
        {
            "nom": "Créatine monohydrate",
            "marque": "Optimum Nutrition",
            "magasin": "En ligne",
            "categorie": "Suppléments",
            "calories": 0,
            "proteines": 0,
            "glucides": 0,
            "lipides": 0,
            "fibres": 0,
            "prix_kg": 60,
        },
        {
            "nom": "BCAA",
            "marque": "Scitec Nutrition",
            "magasin": "En ligne",
            "categorie": "Suppléments",
            "calories": 0,
            "proteines": 0,
            "glucides": 0,
            "lipides": 0,
            "fibres": 0,
            "prix_kg": 80,
        },
        {
            "nom": "Caséine micellaire",
            "marque": "MyProtein",
            "magasin": "En ligne",
            "categorie": "Suppléments",
            "calories": 368,
            "proteines": 90,
            "glucides": 3,
            "lipides": 1.5,
            "fibres": 0,
            "prix_kg": 35,
        },
        {
            "nom": "Protéine végétale",
            "marque": "SunWarrior",
            "magasin": "En ligne",
            "categorie": "Suppléments",
            "calories": 395,
            "proteines": 70,
            "glucides": 13,
            "lipides": 6,
            "fibres": 5,
            "prix_kg": 45,
        },
    ]

    # Combiner tous les aliments
    all_aliments = (
        aliments_proteines
        + aliments_feculents
        + aliments_legumes
        + aliments_fruits
        + aliments_laitiers
        + aliments_noix
        + aliments_supplements
    )

    # Ajouter les aliments à la base de données
    aliment_ids = {}  # Pour stocker les IDs des aliments ajoutés
    for aliment in all_aliments:
        aliment_id = db.ajouter_aliment(aliment)
        aliment_ids[aliment["nom"]] = aliment_id

    print(f"✓ {len(all_aliments)} aliments ajoutés")

    # ----------------------
    # Ajouter des repas types (recettes)
    # ----------------------

    # Petit-déjeuner protéiné
    petit_dej = {
        "nom": "Petit-déjeuner protéiné",
        "description": "Parfait pour commencer la journée avec de l'énergie et des protéines",
        "aliments": [
            {"nom": "Fromage blanc 0%", "quantite": 200},
            {"nom": "Banane", "quantite": 120},
            {"nom": "Myrtilles", "quantite": 50},
            {"nom": "Graines de chia", "quantite": 15},
            {"nom": "Amandes", "quantite": 20},
        ],
    }

    # Déjeuner poulet/riz
    dejeuner_poulet = {
        "nom": "Bowl poulet/riz/légumes",
        "description": "Repas équilibré riche en protéines et glucides complexes",
        "aliments": [
            {"nom": "Poulet (blanc)", "quantite": 150},
            {"nom": "Riz blanc", "quantite": 80},
            {"nom": "Brocoli", "quantite": 100},
            {"nom": "Carottes", "quantite": 100},
            {"nom": "Amandes", "quantite": 10},
        ],
    }

    # Snack protéiné
    snack = {
        "nom": "Snack protéiné",
        "description": "Collation riche en protéines pour l'après-entraînement",
        "aliments": [
            {"nom": "Skyr", "quantite": 150},
            {"nom": "Whey protéine", "quantite": 30},
            {"nom": "Pomme", "quantite": 150},
        ],
    }

    # Dîner saumon
    diner_saumon = {
        "nom": "Saumon et légumes",
        "description": "Dîner léger riche en protéines et acides gras essentiels",
        "aliments": [
            {"nom": "Filet de saumon", "quantite": 150},
            {"nom": "Patate douce", "quantite": 150},
            {"nom": "Épinards", "quantite": 150},
            {"nom": "Cottage cheese", "quantite": 100},
        ],
    }

    # Bowl veggie
    bowl_veggie = {
        "nom": "Bowl végétarien protéiné",
        "description": "Option végétarienne riche en protéines",
        "aliments": [
            {"nom": "Quinoa", "quantite": 80},
            {"nom": "Cottage cheese", "quantite": 150},
            {"nom": "Brocoli", "quantite": 100},
            {"nom": "Poivron rouge", "quantite": 100},
            {"nom": "Noix de cajou", "quantite": 20},
        ],
    }

    recipes = [petit_dej, dejeuner_poulet, snack, diner_saumon, bowl_veggie]

    # Ajouter les recettes
    for recipe in recipes:
        # Créer le repas type
        repas_type_id = db.ajouter_repas_type(recipe["nom"], recipe["description"])

        # Ajouter les aliments au repas type
        for aliment in recipe["aliments"]:
            aliment_id = aliment_ids[aliment["nom"]]
            db.ajouter_aliment_repas_type(
                repas_type_id, aliment_id, aliment["quantite"]
            )

    print(f"✓ {len(recipes)} repas types (recettes) ajoutés")
    print("\nBase de données initialisée avec succès!")


if __name__ == "__main__":
    seed_database()
