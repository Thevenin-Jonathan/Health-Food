# Remplacer l'importation relative par une importation absolue
from src.database.models.aliment import Aliment


class AlimentQuantifie:
    """Un aliment avec sa quantité dans un repas"""

    def __init__(self, aliment, quantite):
        self.aliment = aliment
        self.quantite = quantite

    @property
    def valeurs_nutritives(self):
        """Retourne les valeurs nutritives pour la quantité de cet aliment"""
        return self.aliment.valeur_nutritive_pour_quantite(self.quantite)

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        aliment_dict = self.aliment.to_dict()
        aliment_dict["quantite"] = self.quantite
        return aliment_dict


class Repas:
    """Représente un repas composé d'aliments avec quantités"""

    def __init__(self, id=None, nom="", jour="", ordre=0, semaine_id=None):
        self.id = id
        self.nom = nom
        self.jour = jour
        self.ordre = ordre
        self.semaine_id = semaine_id
        self.aliments = []  # Liste d'objets AlimentQuantifie

    def ajouter_aliment(self, aliment, quantite):
        """Ajoute un aliment avec sa quantité au repas"""
        self.aliments.append(AlimentQuantifie(aliment, quantite))

    def supprimer_aliment(self, aliment_id):
        """Supprime un aliment du repas par son ID"""
        self.aliments = [a for a in self.aliments if a.aliment.id != aliment_id]

    @property
    def total_calories(self):
        """Calcule le total des calories du repas"""
        return sum(a.valeurs_nutritives["calories"] for a in self.aliments)

    @property
    def total_proteines(self):
        """Calcule le total des protéines du repas"""
        return sum(a.valeurs_nutritives["proteines"] for a in self.aliments)

    @property
    def total_glucides(self):
        """Calcule le total des glucides du repas"""
        return sum(a.valeurs_nutritives["glucides"] for a in self.aliments)

    @property
    def total_lipides(self):
        """Calcule le total des lipides du repas"""
        return sum(a.valeurs_nutritives["lipides"] for a in self.aliments)

    @property
    def totaux(self):
        """Renvoie un dictionnaire avec tous les totaux du repas"""
        return {
            "calories": self.total_calories,
            "proteines": self.total_proteines,
            "glucides": self.total_glucides,
            "lipides": self.total_lipides,
        }

    @classmethod
    def from_dict(cls, data, aliments=None):
        """Crée une instance à partir d'un dictionnaire et d'une liste d'aliments optionnelle"""
        repas = cls(
            id=data.get("id"),
            nom=data.get("nom", ""),
            jour=data.get("jour", ""),
            ordre=data.get("ordre", 0),
            semaine_id=data.get("semaine_id"),
        )

        # Si des aliments sont fournis, les ajouter
        if aliments:
            for aliment_data in aliments:
                aliment = Aliment.from_dict(aliment_data)
                repas.ajouter_aliment(aliment, aliment_data.get("quantite", 0))

        return repas

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            "id": self.id,
            "nom": self.nom,
            "jour": self.jour,
            "ordre": self.ordre,
            "semaine_id": self.semaine_id,
            "aliments": [a.to_dict() for a in self.aliments],
            "total_calories": self.total_calories,
            "total_proteines": self.total_proteines,
            "total_glucides": self.total_glucides,
            "total_lipides": self.total_lipides,
        }

    def __str__(self):
        return f"{self.nom} ({self.jour}, ordre {self.ordre})"
