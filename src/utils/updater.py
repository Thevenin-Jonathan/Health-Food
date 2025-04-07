import os
import sys
import json
import subprocess
import time
import urllib.request
from urllib.error import URLError
from packaging import version
from PySide6.QtCore import QObject, Signal, QThread


class UpdateWorker(QThread):
    """Thread de travail pour les opérations de mise à jour"""

    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)
    download_progress = Signal(int, int)  # reçu, total

    def __init__(self, current_version, update_url):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url
        self.should_cancel = False
        self.timeout = 1000
        self.retry_count = 1

    def run(self):
        retry_count = getattr(self, "retry_count", 1)
        timeout = getattr(self, "timeout", 5000) / 1000  # Convertir en secondes

        for attempt in range(retry_count):
            try:
                # Télécharger avec timeout
                with urllib.request.urlopen(
                    self.update_url, timeout=timeout
                ) as response:
                    update_info = json.loads(response.read().decode("utf-8"))

                # Si réussi, sortir de la boucle
                if version.parse(update_info["version"]) > version.parse(
                    self.current_version
                ):
                    self.update_available.emit(update_info)
                else:
                    self.no_update.emit()
                return

            except URLError as e:
                if attempt < retry_count - 1:
                    print(f"Tentative {attempt+1} échouée, nouvelle tentative...")
                    continue
                self.error.emit(f"Erreur de connexion: {str(e)}")
            except json.JSONDecodeError as e:
                self.error.emit(f"Erreur de décodage JSON: {str(e)}")
                break
            except ValueError as e:
                self.error.emit(f"Erreur de valeur: {str(e)}")
                break
            except (OSError, IOError) as e:
                self.error.emit(f"Erreur système ou d'entrée/sortie: {str(e)}")
                break

    def download_update(self, download_url, save_path):
        """Télécharger la mise à jour"""
        try:
            # Créer un dossier temporaire si nécessaire
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Télécharger avec suivi de progression
            with urllib.request.urlopen(download_url) as response:
                file_size = int(response.info().get("Content-Length", 0))
                bytes_downloaded = 0
                block_size = 8192

                with open(save_path, "wb") as f:
                    while True:
                        if self.should_cancel:
                            return False

                        buffer = response.read(block_size)
                        if not buffer:
                            break

                        bytes_downloaded += len(buffer)
                        f.write(buffer)

                        if file_size:
                            self.download_progress.emit(bytes_downloaded, file_size)

            return True

        except (URLError, OSError, IOError) as e:
            self.error.emit(f"Erreur lors du téléchargement: {str(e)}")
            return False

    def cancel(self):
        """Annuler les opérations en cours"""
        self.should_cancel = True


class UpdateManager(QObject):
    """Gestionnaire des mises à jour de l'application"""

    update_available = Signal(dict)
    update_progress = Signal(int)  # 0-100%
    update_complete = Signal()
    update_error = Signal(str)

    def __init__(self, app_version="1.0.0", parent=None):
        super().__init__(parent)
        self.app_version = app_version
        self.update_url = "https://raw.githubusercontent.com/Thevenin-Jonathan/Health-Food/refs/heads/main/update_info.json"
        self.worker = None
        self.downloads_dir = os.path.join(
            os.path.expanduser("~"), "AppData", "Local", "HealthAndFood", "Updates"
        )

        # Créer le répertoire de téléchargement s'il n'existe pas
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Nettoyer les anciens fichiers de mise à jour
        self.cleanup_old_installers()

        self._silent_check = False

    def check_for_updates(self, silent=False):
        """Vérifier si des mises à jour sont disponibles"""
        # Annuler les opérations précédentes si elles existent
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()

        # Créer un nouveau thread de travail
        self.worker = UpdateWorker(self.app_version, self.update_url)
        self.worker.update_available.connect(self._on_update_available)
        self.worker.no_update.connect(self._on_no_update)
        self.worker.error.connect(self._on_error)
        self.worker.timeout = 10000
        self.worker.retry_count = 3
        self.worker.start()
        self._silent_check = silent

    def download_update(self, update_info):
        """Télécharger la mise à jour"""
        # Générer un nom de fichier basé sur la version
        filename = os.path.basename(update_info["download_url"])
        save_path = os.path.join(self.downloads_dir, filename)

        # Démarrer le téléchargement dans le thread
        if self.worker and self.worker.isRunning():
            self.worker.wait()  # Attendre la fin de la vérification

        # Créer un nouveau thread pour le téléchargement
        self.worker = UpdateWorker(self.app_version, self.update_url)
        self.worker.error.connect(self._on_error)
        self.worker.download_progress.connect(self._on_download_progress)

        # Démarrer le téléchargement dans un thread séparé
        self.worker.start()
        success = self.worker.download_update(update_info["download_url"], save_path)

        if success:
            return save_path
        return None

    def install_update(self, installer_path):
        """Lancer l'installation de la mise à jour"""
        try:
            if not os.path.exists(installer_path):
                self.update_error.emit(
                    f"Le fichier d'installation est introuvable: {installer_path}"
                )
                return False

            # Lancer l'installeur
            subprocess.Popen([installer_path], shell=True)

            # Signaler que l'application va se fermer pour mise à jour
            self.update_complete.emit()

            # Attendre un moment pour que l'utilisateur voie le message
            time.sleep(2)

            # Quitter l'application pour permettre l'installation
            sys.exit(0)

        except FileNotFoundError as e:
            self.update_error.emit(
                f"Fichier introuvable lors du lancement de l'installation: {str(e)}"
            )
            return False
        except OSError as e:
            self.update_error.emit(
                f"Erreur système lors du lancement de l'installation: {str(e)}"
            )
            return False

    def cleanup_old_installers(self, keep_latest=True, days_to_keep=30):
        """Nettoie les anciens fichiers d'installation"""
        try:
            if not os.path.exists(self.downloads_dir):
                return

            files = [
                os.path.join(self.downloads_dir, f)
                for f in os.listdir(self.downloads_dir)
                if os.path.isfile(os.path.join(self.downloads_dir, f))
                and f.endswith(".exe")
            ]

            # Rien à nettoyer
            if not files:
                return

            # Trier par date de modification (du plus récent au plus ancien)
            files.sort(key=os.path.getmtime, reverse=True)

            # Garder le fichier le plus récent si demandé
            start_index = 1 if keep_latest and files else 0

            # Supprimer les fichiers plus anciens que days_to_keep jours
            current_time = time.time()

            for file_path in files[start_index:]:
                file_age_days = (current_time - os.path.getmtime(file_path)) / (
                    24 * 3600
                )
                if file_age_days > days_to_keep:
                    try:
                        os.remove(file_path)
                        print(
                            f"Ancien installateur supprimé : {os.path.basename(file_path)}"
                        )
                    except OSError as e:
                        print(f"Impossible de supprimer {file_path}: {e}")

        except (OSError, IOError) as e:
            print(
                f"Erreur système ou d'entrée/sortie lors du nettoyage des installateurs: {e}"
            )
        except ValueError as e:
            print(f"Erreur de valeur lors du nettoyage des installateurs: {e}")

    def _on_update_available(self, update_info):
        """Traiter la disponibilité d'une mise à jour"""
        if not self._silent_check:
            self.update_available.emit(update_info)

    def _on_no_update(self):
        """Aucune mise à jour disponible"""
        if not self._silent_check:
            print("Aucune mise à jour disponible.")

    def _on_error(self, error_message):
        """Gérer les erreurs de mise à jour"""
        if not self._silent_check:
            self.update_error.emit(error_message)

    def _on_download_progress(self, received, total):
        """Mettre à jour la progression du téléchargement"""
        if total > 0:
            progress = int((received / total) * 100)
            self.update_progress.emit(progress)
