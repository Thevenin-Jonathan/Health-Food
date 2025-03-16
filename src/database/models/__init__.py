# Utilisez des importations absolues au lieu de relatives
from src.database.models.aliment import Aliment
from src.database.models.repas import Repas, AlimentQuantifie
from src.database.models.semaine import Semaine

# Pour faciliter l'importation
__all__ = ["Aliment", "Repas", "AlimentQuantifie", "Semaine"]
