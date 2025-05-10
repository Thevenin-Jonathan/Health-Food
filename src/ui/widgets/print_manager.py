import tempfile
import os
import time
from PySide6.QtGui import QTextDocument, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import QMessageBox, QDialog
from src.ui.dialogs.print_preview_dialog import PrintPreviewDialog
from src.utils import JOURS_SEMAINE
from src.utils.browser_launcher import launch_browser_with_file


class PrintManager:
    """Gestion de l'impression du planning"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.temp_files = []  # Pour suivre les fichiers temporaires

    def print_planning(self, semaine_id):
        """Imprime le planning de la semaine actuelle ou l'ouvre dans le navigateur"""
        # Générer le contenu HTML pour l'impression
        content = self.generate_print_content(semaine_id)

        # Demander à l'utilisateur s'il veut imprimer ou ouvrir dans le navigateur
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Option d'affichage du planning")
        msg_box.setText("Comment souhaitez-vous visualiser le planning?")
        print_button = msg_box.addButton("Aperçu et impression", QMessageBox.ActionRole)
        browser_button = msg_box.addButton(
            "Ouvrir dans le navigateur", QMessageBox.ActionRole
        )
        msg_box.addButton("Annuler", QMessageBox.RejectRole)

        msg_box.exec()

        if msg_box.clickedButton() == print_button:
            self._show_print_dialog(content)
        elif msg_box.clickedButton() == browser_button:
            self._open_in_browser(content)

    def _show_print_dialog(self, content):
        """Affiche la boîte de dialogue d'aperçu et d'impression"""
        # Afficher une boîte de dialogue d'aperçu avant impression
        preview_dialog = PrintPreviewDialog(content)
        if preview_dialog.exec() == QDialog.Accepted:
            # Création d'une imprimante et configuration
            printer = QPrinter(QPrinter.HighResolution)

            # Configuration en format paysage pour avoir tous les jours sur une seule page
            printer.setPageOrientation(QPageLayout.Landscape)

            # Afficher la boîte de dialogue d'impression
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec():
                # Créer et remplir un document texte
                document = QTextDocument()

                # Désactiver les marges internes du document
                document.setDocumentMargin(0)

                # Charger le contenu HTML
                document.setHtml(content)

                # Imprimer le document
                document.print_(printer)

    def _open_in_browser(self, content):
        """Ouvre le contenu HTML dans un navigateur web directement"""
        # Créer un fichier temporaire avec extension .html qui ne sera pas supprimé automatiquement
        try:
            # Créer un nom de fichier unique dans le dossier temp
            file_name = f"planning_{int(time.time())}.html"
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file_name)

            # Écrire le contenu HTML dans le fichier
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()  # Forcer l'écriture sur le disque
                os.fsync(
                    f.fileno()
                )  # S'assurer que les données sont écrites physiquement

            # Ajouter une petite pause pour s'assurer que le fichier est bien écrit
            time.sleep(0.2)

            # Garder une référence au fichier pour éviter qu'il soit supprimé
            self.temp_files.append(file_path)

            # Ouvrir le fichier dans le navigateur
            success = launch_browser_with_file(file_path)

            if success:
                print(f"Fichier ouvert avec succès: {file_path}")
            else:
                # Si l'ouverture a échoué, informer l'utilisateur
                QMessageBox.warning(
                    None,
                    "Problème d'ouverture",
                    f"Impossible d'ouvrir automatiquement le fichier dans un navigateur.\n\n"
                    f"Le planning a été enregistré dans:\n{file_path}\n\n"
                    f"Veuillez l'ouvrir manuellement avec votre navigateur.",
                )

        except Exception as e:
            QMessageBox.critical(
                None,
                "Erreur",
                f"Impossible d'ouvrir le planning dans le navigateur: {str(e)}",
            )
            print(f"Erreur d'ouverture du fichier HTML: {e}")
            import traceback

            traceback.print_exc()

    def __del__(self):
        """Nettoyage des fichiers temporaires à la destruction de l'objet"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    def cleanup_temp_files(self, delay=30):
        """Nettoie les fichiers temporaires après un certain délai"""
        for file_path in self.temp_files:
            try:
                if (
                    os.path.exists(file_path)
                    and (time.time() - os.path.getctime(file_path)) > delay
                ):
                    os.remove(file_path)
            except Exception as e:
                print(
                    f"Erreur lors de la suppression du fichier temporaire {file_path}: {e}"
                )

    def generate_print_content(self, semaine_id):
        """Génère le contenu HTML du planning pour l'impression"""
        # Récupérer les données de la semaine
        repas_semaine = self.db_manager.get_repas_semaine(semaine_id)

        # Créer le document HTML avec un style optimisé pour l'impression
        html = "<html><head>"
        html += "<meta charset='UTF-8'>"
        html += "<style>"
        html += "body { font-family: Arial, sans-serif; margin: 0; padding: 0; width: 100%; }"
        html += "table { width: 100%; border-collapse: collapse; table-layout: fixed; }"
        html += "th { background-color: #f2f2f2; padding: 2px; border: 2px solid #000; font-weight: bold; font-size: 8pt; text-align: center; }"
        html += "td { border: 2px solid #000; padding: 4px 2px; vertical-align: top; font-size: 8pt; width: 14%; }"
        html += ".repas { margin-bottom: 6px; page-break-inside: avoid; }"
        html += ".repas-title { font-weight: bold; margin-top: 2px; margin-bottom: 2px; font-size: 7pt; }"
        html += ".aliment { margin-left: 10px; margin-bottom: 2px; font-size: 6pt; }"
        html += "* { -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }"
        html += "@page { size: landscape; margin: 1cm; }"
        html += "</style>"
        html += "</head><body>"

        # Créer directement le tableau
        html += "<table>"

        # En-tête du tableau
        html += "<tr>"
        for jour in JOURS_SEMAINE:
            html += f"<th>{jour}</th>"
        html += "</tr>"

        # Contenu du tableau
        html += "<tr>"
        for jour in JOURS_SEMAINE:
            html += "<td>"

            for repas in repas_semaine[jour]:
                html += "<div class='repas'>"
                html += f"<div class='repas-title'>{repas['nom']}</div>"

                if repas["aliments"]:
                    for aliment in repas["aliments"]:
                        html += f"<div class='aliment'>• {aliment['nom']} ({aliment['quantite']}g)</div>"
                else:
                    html += "<div class='aliment'>Aucun aliment</div>"

                html += "</div>"

            html += "</td>"

        html += "</tr>"
        html += "</table>"
        html += "</body></html>"

        return html
