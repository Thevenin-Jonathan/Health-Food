import os
import subprocess
import platform
import webbrowser
import winreg
import time


def launch_browser_with_file(file_path):
    """
    Ouvre un fichier HTML dans un navigateur Web, en contournant les associations de fichiers du système.
    Cette fonction essaiera plusieurs approches pour s'assurer que le fichier s'ouvre dans un navigateur.

    Args:
        file_path (str): Chemin absolu vers le fichier HTML à ouvrir

    Returns:
        bool: True si l'ouverture a réussi, False sinon
    """
    file_path = os.path.abspath(file_path)

    # Vérifier que le fichier existe bien
    if not os.path.exists(file_path):
        print(f"Erreur: Le fichier {file_path} n'existe pas!")
        return False

    # Créer une URL valide avec file://
    file_url = f"file:///{file_path.replace('\\', '/')}"

    # 1. D'abord essayer avec les navigateurs courants sur Windows
    if platform.system() == "Windows":
        browser_paths = find_windows_browsers()

        # Trier pour que Edge soit en premier s'il existe
        browser_paths = dict(
            sorted(browser_paths.items(), key=lambda x: x[0] != "Edge")
        )

        for browser_name, browser_path in browser_paths.items():
            try:
                if os.path.exists(browser_path):
                    # Lancer le processus du navigateur avec le fichier
                    cmd = [browser_path, file_url]
                    subprocess.Popen(cmd)
                    time.sleep(0.5)  # Petite pause pour laisser le processus démarrer
                    return True
            except Exception as e:
                print(f"Échec avec {browser_name}: {e}")
                continue

    # 2. Essayer avec l'ouverture directe du navigateur par défaut
    try:
        print("Tentative avec webbrowser.open")
        if webbrowser.open(file_url):
            time.sleep(0.5)  # Pause pour s'assurer que le navigateur démarre
            return True
    except Exception as e:
        print(f"Échec de webbrowser.open: {e}")

    # 3. Dernière tentative avec les commandes spécifiques à la plateforme
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":  # macOS
            subprocess.call(["open", file_path])
        else:  # Linux
            subprocess.call(["xdg-open", file_path])
        time.sleep(0.5)  # Pause pour s'assurer que le navigateur démarre
        return True
    except Exception as e:
        print(f"Échec de la commande spécifique à la plateforme: {e}")
        return False


def find_windows_browsers():
    """
    Trouve les chemins vers les principaux navigateurs installés sur Windows.

    Returns:
        dict: Dictionnaire avec les noms de navigateurs et leurs chemins
    """
    browsers = {}

    # Chemins possibles pour les navigateurs courants (versions 64 et 32 bits)
    browser_locations = {
        "Chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "Firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "Edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
    }

    # Vérifier si les navigateurs existent
    for browser, paths in browser_locations.items():
        for path in paths:
            if os.path.exists(path):
                browsers[browser] = path
                break

    # Si aucun navigateur n'a été trouvé, essayer de les trouver dans le registre Windows
    if not browsers and platform.system() == "Windows":
        try:
            # Chrome
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            ) as key:
                browsers["Chrome"] = winreg.QueryValue(key, None)
        except Exception:
            pass

        try:
            # Firefox
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe",
            ) as key:
                browsers["Firefox"] = winreg.QueryValue(key, None)
        except Exception:
            pass

        try:
            # Edge
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
            ) as key:
                browsers["Edge"] = winreg.QueryValue(key, None)
        except Exception:
            pass

    return browsers
