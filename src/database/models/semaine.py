from src.utils.config import JOURS_SEMAINE
from src.database.models.repas import Repas


class Semaine:
    """Représente une semaine contenant des repas pour chaque jour"""

    def __init__(self, id):
        self.id = id
        self.repas = {jour: [] for jour in JOURS_SEMAINE}
        self.nom_personnalise = None

    def ajouter_repas(self, repas):
        """Ajoute un repas au jour correspondant"""
        jour = repas.jour
        if jour in self.repas:
            # Insérer le repas au bon ordre
            position = 0
            for i, r in enumerate(self.repas[jour]):
                if r.ordre > repas.ordre:
                    position = i
                    break
                position = i + 1

            self.repas[jour].insert(position, repas)
        else:
            # Jour inconnu, on l'ajoute quand même
            self.repas[jour] = [repas]

    def supprimer_repas(self, repas_id):
        """Supprime un repas par son ID"""
        for jour in self.repas:
            self.repas[jour] = [r for r in self.repas[jour] if r.id != repas_id]

    def get_total_jour(self, jour):
        """Calcule les totaux nutritionnels pour un jour"""
        repas_jour = self.repas.get(jour, [])
        if not repas_jour:
            return {"calories": 0, "proteines": 0, "glucides": 0, "lipides": 0}

        # Calculer les totaux
        total_cal = sum(r.total_calories for r in repas_jour)
        total_prot = sum(r.total_proteines for r in repas_jour)
        total_gluc = sum(r.total_glucides for r in repas_jour)
        total_lip = sum(r.total_lipides for r in repas_jour)

        return {
            "calories": total_cal,
            "proteines": total_prot,
            "glucides": total_gluc,
            "lipides": total_lip,
        }

    def get_total_semaine(self):
        """Calcule les totaux nutritionnels pour toute la semaine"""
        totaux = {"calories": 0, "proteines": 0, "glucides": 0, "lipides": 0}

        for jour in self.repas:
            jour_totaux = self.get_total_jour(jour)
            for key in totaux:
                totaux[key] += jour_totaux[key]

        return totaux

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            "id": self.id,
            "nom_personnalise": self.nom_personnalise,
            "repas": {
                jour: [r.to_dict() for r in repas] for jour, repas in self.repas.items()
            },
            "totaux": self.get_total_semaine(),
        }

    @property
    def nom(self):
        """Retourne le nom à afficher pour la semaine"""
        if self.nom_personnalise:
            return self.nom_personnalise
        return f"Semaine {self.id}"

    @nom.setter
    def nom(self, value):
        """Définit le nom personnalisé de la semaine"""
        self.nom_personnalise = value

    def __str__(self):
        return self.nom
