import os
import sys
import subprocess


def restart_application():
    """Redémarre l'application"""
    try:
        # Si nous sommes dans un environnement PyInstaller
        if getattr(sys, "frozen", False):
            # Redémarrer le fichier exécutable
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            # En mode développement, utiliser subprocess
            args = [sys.executable] + sys.argv
            subprocess.Popen(args)
            # Quitter l'application actuelle
            sys.exit()
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Erreur lors du redémarrage de l'application: {e}")
        sys.exit(1)
