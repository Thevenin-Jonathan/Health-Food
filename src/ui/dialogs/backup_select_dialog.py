import os
import datetime
import sqlite3
import tempfile
import shutil
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QPushButton,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
    QGridLayout,
    QProgressBar,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QFontMetrics


class BackupPreviewWidget(QGroupBox):
    """Widget d'aperçu pour afficher les statistiques d'une sauvegarde"""

    def __init__(self, parent=None):
        super().__init__("Aperçu de la sauvegarde", parent)

        self.setObjectName("preview-group")
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setColumnStretch(1, 1)  # La colonne des valeurs s'étire
        self.grid_layout.setVerticalSpacing(10)  # Plus d'espace entre les lignes
        self.grid_layout.setContentsMargins(20, 25, 20, 20)  # Marges pour plus d'espace

        self.db_path = None
        self.temp_dir = None

        # Créer les étiquettes pour les statistiques
        row = 0
        self.labels = {}

        for label_text in [
            "Date de sauvegarde:",
            "Taille du fichier:",
            "Profil utilisateur:",
            "Aliments:",
            "Repas:",
            "Semaines de planning:",
            "Repas types:",
        ]:
            # Étiquette de titre (à gauche)
            title = QLabel(label_text)
            title.setFont(QFont(title.font().family(), weight=QFont.Bold))
            title.setProperty("class", "stats-title")  # Pour le style QSS
            self.grid_layout.addWidget(title, row, 0, Qt.AlignRight)

            # Étiquette de valeur (à droite)
            value = QLabel("—")
            value.setProperty("class", "stats-value")  # Pour le style QSS
            value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            key = label_text.replace(":", "").lower().replace(" ", "_")
            self.labels[key] = value
            self.grid_layout.addWidget(value, row, 1, Qt.AlignLeft)

            row += 1

        # Barre de progression pour l'analyse
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.grid_layout.addWidget(self.progress_bar, row, 0, 1, 2)

        # Message de statut
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "hint")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self.status_label, row + 1, 0, 1, 2)

        # Timer pour simuler une progression
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.current_progress = 0

    def reset(self):
        """Réinitialise l'aperçu"""
        for label in self.labels.values():
            label.setText("—")
        self.status_label.setText("")
        self.progress_bar.setVisible(False)

    def set_analyzing(self, is_analyzing):
        """Affiche ou masque l'état d'analyse"""
        if is_analyzing:
            self.status_label.setText("Analyse de la sauvegarde en cours...")
            self.progress_bar.setVisible(True)
            self.current_progress = 0
            self.progress_bar.setValue(0)
            self.timer.start(50)  # Mise à jour toutes les 50ms
        else:
            self.status_label.setText("")
            self.progress_bar.setVisible(False)
            self.timer.stop()

    def update_progress(self):
        """Met à jour la barre de progression de manière animée"""
        self.current_progress += 3
        if self.current_progress >= 100:
            self.current_progress = 100
            self.timer.stop()
        self.progress_bar.setValue(self.current_progress)

    def analyze_backup(self, backup_path):
        """Analyse le contenu de la sauvegarde et met à jour l'aperçu"""
        self.reset()

        if not backup_path or not os.path.exists(backup_path):
            return False

        self.db_path = backup_path

        # Mettre à jour les informations de base du fichier
        file_size = os.path.getsize(backup_path) / (1024 * 1024)  # Taille en Mo
        self.labels["taille_du_fichier"].setText(f"{file_size:.2f} Mo")

        # Extraire la date de la sauvegarde
        try:
            filename = os.path.basename(backup_path)
            date_part = filename.split(".")[-2]
            if len(date_part) == 15:  # Format YYYYMMDD_HHMMSS
                date_obj = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S")
                self.labels["date_de_sauvegarde"].setText(
                    date_obj.strftime("%d/%m/%Y %H:%M:%S")
                )
            else:
                # Utiliser la date de modification du fichier
                mod_time = os.path.getmtime(backup_path)
                date_obj = datetime.datetime.fromtimestamp(mod_time)
                self.labels["date_de_sauvegarde"].setText(
                    date_obj.strftime("%d/%m/%Y %H:%M:%S")
                )
        except:
            self.labels["date_de_sauvegarde"].setText("Date inconnue")

        # Montrer la barre de progression pendant l'analyse
        self.set_analyzing(True)

        # Lancer l'analyse dans un thread séparé pour ne pas bloquer l'interface
        QTimer.singleShot(300, lambda: self._analyze_db_content(backup_path))

        return True

    # Dans la classe BackupPreviewWidget, mettez à jour la méthode _analyze_db_content

    def _analyze_db_content(self, db_path):
        """Analyse le contenu de la base de données"""
        conn = None
        self.temp_dir = None
        temp_db_path = None

        try:
            # Créer un dossier temporaire pour la copie
            self.temp_dir = tempfile.mkdtemp()
            temp_db_path = os.path.join(self.temp_dir, "temp_db.sqlite")

            # Copier la base de données pour l'analyser sans risque
            shutil.copy2(db_path, temp_db_path)

            # Analyser le contenu
            try:
                conn = sqlite3.connect(temp_db_path)
                conn.row_factory = sqlite3.Row  # Pour accéder aux noms de colonnes
                cursor = conn.cursor()

                # Trouver toutes les tables existantes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(
                    f"Tables trouvées: {tables}"
                )  # Afficher les tables pour le débogage

                # Noms exacts des tables (basés sur le code de db_connector.py)
                TABLE_UTILISATEUR = "utilisateur"
                TABLE_ALIMENTS = "aliments"
                TABLE_SEMAINES = "semaines"
                TABLE_REPAS = "repas"
                TABLE_REPAS_ALIMENTS = "repas_aliments"
                TABLE_REPAS_TYPES = "repas_types"

                # Vérifier les statistiques utilisateur
                if TABLE_UTILISATEUR in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_UTILISATEUR}")
                    utilisateur_count = cursor.fetchone()[0]
                    if utilisateur_count > 0:
                        # Récupérer le nom de l'utilisateur
                        cursor.execute(f"SELECT nom FROM {TABLE_UTILISATEUR} LIMIT 1")
                        user_name = cursor.fetchone()[0]
                        self.labels["profil_utilisateur"].setText(
                            f"{user_name}" if user_name else "Profil existant"
                        )
                    else:
                        self.labels["profil_utilisateur"].setText("Aucun profil")
                else:
                    self.labels["profil_utilisateur"].setText("Table non trouvée")

                # Compter les aliments
                if TABLE_ALIMENTS in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_ALIMENTS}")
                    aliments_count = cursor.fetchone()[0]
                    self.labels["aliments"].setText(
                        f"{aliments_count} aliment{'s' if aliments_count != 1 else ''}"
                    )
                else:
                    self.labels["aliments"].setText("Table non trouvée")

                # Compter les semaines de planning
                if TABLE_SEMAINES in tables:
                    try:
                        # D'abord, compter simplement les entrées dans la table semaines
                        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_SEMAINES}")
                        semaines_count = cursor.fetchone()[0]

                        # Ensuite, vérifier s'il y a des repas associés à ces semaines
                        if TABLE_REPAS in tables:
                            cursor.execute(
                                f"""
                                SELECT COUNT(DISTINCT semaine_id) 
                                FROM {TABLE_REPAS}
                                WHERE semaine_id IS NOT NULL
                            """
                            )
                            semaines_avec_repas = cursor.fetchone()[0]

                            # Si nous trouvons des semaines avec des repas
                            if semaines_avec_repas > 0:
                                self.labels["semaines_de_planning"].setText(
                                    f"{semaines_avec_repas} semaine{'s' if semaines_avec_repas != 1 else ''} active{'s' if semaines_avec_repas != 1 else ''}"
                                )
                            else:
                                # S'il y a des semaines mais sans repas
                                self.labels["semaines_de_planning"].setText(
                                    f"{semaines_count} semaine{'s' if semaines_count != 1 else ''} (sans repas)"
                                )
                        else:
                            # Si la table repas n'existe pas
                            self.labels["semaines_de_planning"].setText(
                                f"{semaines_count} semaine{'s' if semaines_count != 1 else ''}"
                            )
                    except sqlite3.Error as e:
                        print(f"Erreur lors du comptage des semaines: {e}")
                        self.labels["semaines_de_planning"].setText(
                            "Erreur de comptage"
                        )
                else:
                    self.labels["semaines_de_planning"].setText("Table non trouvée")

                # Compter les repas types
                if TABLE_REPAS_TYPES in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_REPAS_TYPES}")
                    repas_types_count = cursor.fetchone()[0]
                    self.labels["repas_types"].setText(
                        f"{repas_types_count} repas type{'s' if repas_types_count != 1 else ''}"
                    )
                else:
                    self.labels["repas_types"].setText("Table non trouvée")

                # Compter les repas (en tant que recettes)
                if TABLE_REPAS in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_REPAS}")
                        repas_count = cursor.fetchone()[0]

                        # Récupérer les repas uniques par nom pour compter les "recettes"
                        cursor.execute(f"SELECT COUNT(DISTINCT nom) FROM {TABLE_REPAS}")

                        # Compter les repas qui ont des aliments
                        if TABLE_REPAS_ALIMENTS in tables:
                            cursor.execute(
                                f"""
                                SELECT COUNT(DISTINCT repas_id) 
                                FROM {TABLE_REPAS_ALIMENTS}
                            """
                            )

                            self.labels["repas"].setText(f"{repas_count}")
                        else:
                            self.labels["repas"].setText(
                                f"{repas_count} repas (sans aliments)"
                            )

                    except sqlite3.Error as e:
                        print(f"Erreur lors du comptage des repas: {e}")
                        self.labels["repas"].setText("Erreur de comptage")
                else:
                    self.labels["repas"].setText("Table non trouvée")

                conn.close()

            except sqlite3.Error as e:
                # En cas d'erreur d'accès à la base de données
                print(f"Erreur lors de l'analyse de la base de données: {e}")
                for key in [
                    "profil_utilisateur",
                    "aliments",
                    "semaines_de_planning",
                    "repas_types",
                    "repas",
                ]:
                    self.labels[key].setText("Erreur d'analyse")

            finally:
                # Assurez-vous de fermer la connexion dans tous les cas
                if conn:
                    conn.close()
                    conn = None  # Explicitement marquer comme fermé

            # Terminer l'analyse
            self.set_analyzing(False)
            self.status_label.setText("Analyse terminée")
            self.current_progress = 100
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

        except Exception as e:
            print(f"Erreur lors de l'analyse: {e}")
            self.set_analyzing(False)
            self.status_label.setText(f"Erreur d'analyse: {str(e)}")

        finally:
            # S'assurer que la connexion est fermée
            if conn:
                try:
                    conn.close()
                except:
                    pass

            # Attendre un peu pour que les descripteurs de fichier soient libérés
            try:
                QTimer.singleShot(100, lambda: self._cleanup_temp_files())
            except:
                pass

    def _cleanup_temp_files(self):
        """Nettoie les fichiers temporaires de manière sécurisée"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                for f in os.listdir(self.temp_dir):
                    try:
                        os.remove(os.path.join(self.temp_dir, f))
                    except:
                        pass
                try:
                    os.rmdir(self.temp_dir)
                except:
                    pass
                self.temp_dir = None
            except Exception as e:
                print(f"Erreur lors du nettoyage des fichiers temporaires: {e}")


class BackupSelectDialog(QDialog):
    """Dialogue pour sélectionner une sauvegarde de base de données"""

    def __init__(self, parent=None, backup_dir=None):
        super().__init__(parent)
        self.setWindowTitle("Sélectionner une sauvegarde")
        self.resize(900, 550)
        self.selected_backup = None
        self.backup_dir = backup_dir

        # Améliorer l'espace entre les widgets
        split_spacing = 20  # Plus d'espace entre les panneaux
        general_margins = 15  # Marges générales

        # Créer le layout principal avec plus d'espace
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            general_margins, general_margins, general_margins, general_margins
        )
        main_layout.setSpacing(15)  # Plus d'espace vertical entre les éléments

        # Créer un layout horizontal pour les deux panneaux
        split_layout = QHBoxLayout()
        split_layout.setSpacing(split_spacing)  # Plus d'espace entre les panneaux
        main_layout.addLayout(split_layout)

        # Partie gauche avec la liste des sauvegardes
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Message explicatif
        info_label = QLabel(
            "<b>Restauration de sauvegarde :</b> Sélectionnez une sauvegarde dans la liste ci-dessous. "
            "Les détails de la sauvegarde sélectionnée apparaîtront dans le panneau de droite."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 12px; margin-bottom: 10px; padding: 5px;")
        left_layout.addWidget(info_label)
        left_layout.addSpacing(5)

        # Liste des sauvegardes - CORRECTION: Ne déclarer qu'une seule fois
        self.backup_list = QListWidget()
        self.backup_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.backup_list)

        # Layout pour les boutons de gestion des sauvegardes
        backup_actions_layout = QHBoxLayout()

        # Bouton de suppression
        self.delete_button = QPushButton("Supprimer la sauvegarde")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)  # Désactivé par défaut
        self.delete_button.clicked.connect(self.delete_selected_backup)
        backup_actions_layout.addWidget(self.delete_button)

        # Ajouter un espace extensible
        backup_actions_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        # Bouton pour rafraîchir la liste
        self.refresh_button = QPushButton("Rafraîchir")
        self.refresh_button.clicked.connect(self.refresh_backup_list)
        backup_actions_layout.addWidget(self.refresh_button)

        # Ajouter le layout des actions de sauvegarde
        left_layout.addLayout(backup_actions_layout)

        # Partie droite avec l'aperçu
        self.preview_widget = BackupPreviewWidget()

        # Ajouter les deux panneaux au layout horizontal
        split_layout.addWidget(left_panel, 3)  # Le panneau gauche prend 3/5 de l'espace
        split_layout.addWidget(
            self.preview_widget, 2
        )  # Le panneau droit prend 2/5 de l'espace

        # Boutons standard en bas
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Restaurer")
        button_box.button(QDialogButtonBox.Cancel).setText("Annuler")
        button_box.button(QDialogButtonBox.Cancel).setObjectName("cancelButton")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Remplir la liste des sauvegardes
        self.populate_backup_list()

        # Connecter le double-clic pour accepter directement
        self.backup_list.itemDoubleClicked.connect(self.accept)

        # Connecter la sélection d'élément pour activer/désactiver le bouton de suppression
        self.backup_list.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        """Réagit au changement de sélection dans la liste"""
        current_item = self.backup_list.currentItem()
        self.delete_button.setEnabled(current_item is not None)

        if current_item:
            backup_path = current_item.data(Qt.UserRole)
            self.preview_widget.analyze_backup(backup_path)
        else:
            self.preview_widget.reset()

    def populate_backup_list(self):
        """Remplit la liste avec les sauvegardes disponibles"""
        # Effacer la liste actuelle
        self.backup_list.clear()

        if not self.backup_dir or not os.path.exists(self.backup_dir):
            return

        backup_files = []

        # Trouver tous les fichiers .bak
        for filename in os.listdir(self.backup_dir):
            if filename.endswith(".bak"):
                full_path = os.path.join(self.backup_dir, filename)
                # Obtenir la date de modification
                mod_time = os.path.getmtime(full_path)
                # Obtenir la taille du fichier en Mo
                file_size = os.path.getsize(full_path) / (1024 * 1024)
                backup_files.append((full_path, mod_time, filename, file_size))

        # Trier par date (la plus récente en premier)
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Ajouter à la liste
        for full_path, mod_time, filename, file_size in backup_files:
            # Extraire la date depuis le nom du fichier si possible
            date_str = "Date inconnue"
            date_obj = None

            try:
                # Essayer d'extraire la date du format filename.YYYYMMDD_HHMMSS.bak
                date_part = filename.split(".")[-2]
                if len(date_part) == 15:  # Format YYYYMMDD_HHMMSS
                    date_obj = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S")
                    date_str = date_obj.strftime("%d/%m/%Y %H:%M:%S")
            except (IndexError, ValueError):
                # Si l'extraction échoue, utiliser la date de modification
                date_obj = datetime.datetime.fromtimestamp(mod_time)
                date_str = (
                    date_obj.strftime("%d/%m/%Y %H:%M:%S") + " (dernière modification)"
                )

            # Créer un élément de liste plus informatif sur deux lignes
            display_name = os.path.basename(filename)
            if len(display_name) > 40:
                display_name = display_name[:37] + "..."

            # Ligne 1: Date et heure
            # Ligne 2: Nom du fichier et taille
            item_text = f"{date_str}\n{display_name} ({file_size:.1f} Mo)"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, full_path)

            # Augmenter la taille de l'élément pour accueillir deux lignes
            font_metrics = QFontMetrics(item.font())
            item.setSizeHint(
                QSize(item.sizeHint().width(), max(48, font_metrics.height() * 2 + 16))
            )

            self.backup_list.addItem(item)

        # Sélectionner la première sauvegarde s'il y en a
        if self.backup_list.count() > 0:
            self.backup_list.setCurrentRow(0)

        # Mettre à jour l'état du bouton de suppression
        self.on_selection_changed()

        # Informer l'utilisateur s'il n'y a pas de sauvegardes
        if self.backup_list.count() == 0:
            QMessageBox.information(
                self,
                "Aucune sauvegarde",
                f"Aucune sauvegarde n'a été trouvée dans le dossier:\n{self.backup_dir}\n\n"
                "Utilisez l'option 'Réinitialiser la base de données' avec la case à cocher "
                "'Créer une sauvegarde' pour générer une sauvegarde.",
            )

    def refresh_backup_list(self):
        """Rafraîchit la liste des sauvegardes"""
        self.populate_backup_list()

    def delete_selected_backup(self):
        """Supprime la sauvegarde sélectionnée après confirmation"""
        current_item = self.backup_list.currentItem()
        if not current_item:
            return

        backup_path = current_item.data(Qt.UserRole)
        backup_name = current_item.text()

        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer définitivement cette sauvegarde?\n\n{backup_name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Supprimer le fichier
            os.remove(backup_path)

            # Supprimer l'élément de la liste
            row = self.backup_list.row(current_item)
            self.backup_list.takeItem(row)

            # Mettre à jour l'état du bouton de suppression
            self.on_selection_changed()

            # Informer l'utilisateur
            QMessageBox.information(
                self,
                "Sauvegarde supprimée",
                "La sauvegarde a été supprimée avec succès.",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de suppression",
                f"Une erreur est survenue lors de la suppression de la sauvegarde:\n\n{str(e)}",
            )

    def get_selected_backup(self):
        """Retourne le chemin de la sauvegarde sélectionnée"""
        if self.backup_list.currentItem():
            return self.backup_list.currentItem().data(Qt.UserRole)
        return None
