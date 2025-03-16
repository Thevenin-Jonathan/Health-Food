"""
Utilitaire pour faciliter le chargement des modules et widgets
"""

import importlib
import inspect


class ModuleLoader:
    """
    Classe utilitaire pour charger dynamiquement des modules et classes
    """

    @staticmethod
    def load_class(module_path, class_name):
        """
        Charge dynamiquement une classe à partir de son chemin de module et de son nom

        Args:
            module_path (str): Chemin d'importation du module (ex: 'src.ui.tabs.aliments_tab')
            class_name (str): Nom de la classe à charger (ex: 'AlimentsTab')

        Returns:
            class: La classe chargée
        """
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(
                f"Erreur lors du chargement de la classe {class_name} depuis {module_path}: {e}"
            )
            return None

    @staticmethod
    def get_available_tabs():
        """
        Retourne la liste des onglets disponibles dans src.ui.tabs

        Returns:
            list: Liste des noms de classes d'onglets disponibles
        """
        try:
            # Importer le module des onglets
            tabs_module = importlib.import_module("src.ui.tabs")

            # Récupérer toutes les classes qui héritent de TabBase
            from src.ui.tabs.tab_base import TabBase

            tabs = []
            for name, obj in inspect.getmembers(tabs_module):
                if inspect.isclass(obj) and issubclass(obj, TabBase) and obj != TabBase:
                    tabs.append(name)

            return tabs
        except ImportError as e:
            print(f"Erreur lors du chargement des onglets: {e}")
            return []
