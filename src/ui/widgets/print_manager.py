from PySide6.QtGui import QTextDocument, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from src.ui.dialogs.print_preview_dialog import PrintPreviewDialog
from src.utils.config import JOURS_SEMAINE


class PrintManager:
    """Gestion de l'impression du planning"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def print_planning(self, semaine_id):
        """Imprime le planning de la semaine actuelle"""
        # Générer le contenu HTML pour l'impression
        content = self.generate_print_content(semaine_id)

        # Afficher une boîte de dialogue d'aperçu avant impression
        preview_dialog = PrintPreviewDialog(content)
        if preview_dialog.exec():
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
        html += "th { background-color: #f2f2f2; padding: 12px 5px; border: 2px solid #000; font-weight: bold; font-size: 14pt; text-align: center; }"
        html += "td { border: 2px solid #000; padding: 8px 5px; vertical-align: top; font-size: 12pt; width: 14%; }"
        html += ".repas { margin-bottom: 15px; page-break-inside: avoid; }"
        html += (
            ".repas-title { font-weight: bold; margin-bottom: 8px; font-size: 10pt; }"
        )
        html += ".aliment { margin-left: 10px; margin-bottom: 6px; font-size: 8pt; }"
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
