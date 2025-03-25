from PySide6.QtCore import QObject, Signal
import traceback


class PlanningOperationWorker(QObject):
    """Worker pour exécuter les opérations de planning en arrière-plan"""

    operation_completed = Signal(bool, str, object)

    def __init__(self, db_manager, operation_type, **kwargs):
        """
        Initialise le worker

        Args:
            db_manager: Le gestionnaire de base de données
            operation_type: Le type d'opération (move_repas, copy_repas)
            **kwargs: Arguments spécifiques à l'opération:
                - repas_id: ID du repas à déplacer
                - jour_dest: Jour de destination
                - ordre_dest: Ordre dans le jour de destination
                - semaine_id: ID de la semaine
        """
        super().__init__()
        self.db_manager = db_manager
        self.operation_type = operation_type
        self.kwargs = kwargs

    def run(self):
        """Exécute l'opération demandée dans un thread séparé"""
        try:
            if self.operation_type == "move_repas":
                # Extraire les arguments
                repas_id = self.kwargs.get("repas_id")
                jour_dest = self.kwargs.get("jour_dest")
                ordre_dest = self.kwargs.get("ordre_dest")
                semaine_id = self.kwargs.get("semaine_id")

                # Vérifier que tous les arguments requis sont présents
                if None in (repas_id, jour_dest, ordre_dest):
                    self.operation_completed.emit(
                        False, "Arguments manquants pour le déplacement du repas", None
                    )
                    return

                # Effectuer l'opération
                success = self.db_manager.changer_jour_repas(
                    repas_id, jour_dest, ordre_dest
                )

                if success:
                    # Normaliser les ordres pour s'assurer qu'ils sont consécutifs
                    self.db_manager.normaliser_ordres(jour_dest, semaine_id)

                    # Préparer les données de retour
                    result_data = {"semaine_id": semaine_id}
                    self.operation_completed.emit(
                        True, "Repas déplacé avec succès", result_data
                    )
                else:
                    self.operation_completed.emit(
                        False, "Échec du déplacement du repas", None
                    )

            elif self.operation_type == "copy_repas":
                # Vous pouvez implémenter la copie plus tard si nécessaire
                self.operation_completed.emit(
                    False, "La copie n'est pas encore implémentée", None
                )

            else:
                self.operation_completed.emit(
                    False, f"Opération inconnue: {self.operation_type}", None
                )

        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Erreur dans PlanningOperationWorker: {error_details}")
            self.operation_completed.emit(
                False, f"Erreur lors de l'opération: {str(e)}", None
            )
