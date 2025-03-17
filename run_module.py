"""
Utilitaire pour exécuter des modules individuels du projet
avec le bon contexte d'importation.

Usage:
    python run_module.py path/to/module.py
"""

import sys
import importlib.util
import os


def run_module(module_path):
    """Exécute un module Python avec le bon contexte d'importation"""
    # Assurez-vous que le répertoire racine du projet est dans sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Charger et exécuter le module
    spec = importlib.util.spec_from_file_location("__main__", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_module.py path/to/module.py")
        sys.exit(1)

    module_path = sys.argv[1]
    run_module(module_path)
