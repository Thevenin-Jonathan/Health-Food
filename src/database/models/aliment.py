class Aliment:
    """
    Représente un aliment avec ses valeurs nutritionnelles
    """

    def __init__(
        self,
        id=None,
        nom="",
        marque="",
        magasin="",
        categorie="",
        calories=0,
        proteines=0,
        glucides=0,
        lipides=0,
        fibres=0,
        prix_kg=0,
    ):
        self.id = id
        self.nom = nom
        self.marque = marque
        self.magasin = magasin
        self.categorie = categorie
        self.calories = calories
        self.proteines = proteines
        self.glucides = glucides
        self.lipides = lipides
        self.fibres = fibres
        self.prix_kg = prix_kg

    @classmethod
    def from_dict(cls, data):
        """Crée une instance à partir d'un dictionnaire"""
        return cls(
            id=data.get("id"),
            nom=data.get("nom", ""),
            marque=data.get("marque", ""),
            magasin=data.get("magasin", ""),
            categorie=data.get("categorie", ""),
            calories=data.get("calories", 0),
            proteines=data.get("proteines", 0),
            glucides=data.get("glucides", 0),
            lipides=data.get("lipides", 0),
            fibres=data.get("fibres", 0),
            prix_kg=data.get("prix_kg", 0),
        )

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            "id": self.id,
            "nom": self.nom,
            "marque": self.marque,
            "magasin": self.magasin,
            "categorie": self.categorie,
            "calories": self.calories,
            "proteines": self.proteines,
            "glucides": self.glucides,
            "lipides": self.lipides,
            "fibres": self.fibres,
            "prix_kg": self.prix_kg,
        }

    def valeur_nutritive_pour_quantite(self, quantite):
        """Calcule les valeurs nutritives pour une quantité donnée en grammes"""
        facteur = quantite / 100
        return {
            "calories": self.calories * facteur,
            "proteines": self.proteines * facteur,
            "glucides": self.glucides * facteur,
            "lipides": self.lipides * facteur,
            "fibres": self.fibres * facteur,
        }

    def __str__(self):
        marque_info = f" ({self.marque})" if self.marque else ""
        return f"{self.nom}{marque_info} - {self.calories} kcal/100g"
