from django.core.management.base import BaseCommand
from employees.models import Employe, Evaluation, Formation, InscriptionFormation
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Génère des données de test pour les formations et évaluations de tous les employés'

    def handle(self, *args, **options):
        employes = Employe.objects.all()
        
        if not employes.exists():
            self.stdout.write(self.style.WARNING("Aucun employé trouvé. Veuillez d'abord ajouter des employés."))
            return

        # Création de quelques formations de base
        formations_data = [
            ("Communication Interpersonnelle", "Améliorer la communication au sein des équipes."),
            ("Gestion du Stress", "Techniques et outils pour mieux gérer son stress au quotidien."),
            ("Leadership et Management", "Développer ses compétences de leader."),
            ("Sécurité Informatique", "Sensibilisation aux bonnes pratiques de sécurité."),
            ("Maîtrise d'Excel", "Niveau avancé sur les tableaux croisés dynamiques."),
        ]
        
        formations = []
        for titre, desc in formations_data:
            f, created = Formation.objects.get_or_create(
                titre=titre,
                defaults={
                    'description': desc,
                    'date_debut': date.today() + timedelta(days=random.randint(-60, 30)),
                    'date_fin': date.today() + timedelta(days=random.randint(31, 90)),
                    'budget': random.randint(500, 2000)
                }
            )
            formations.append(f)

        self.stdout.write(f"Traitement de {employes.count()} employés...")

        for emp in employes:
            # 1. Ajouter des évaluations
            num_evals = random.randint(1, 3)
            for i in range(num_evals):
                # On choisit un évaluateur différent de l'employé
                evaluateur = employes.exclude(id=emp.id).order_by('?').first()
                if not evaluateur:
                    evaluateur = emp # Fallback si un seul employé
                
                Evaluation.objects.get_or_create(
                    employe=emp,
                    evaluateur=evaluateur,
                    date=date.today() - timedelta(days=random.randint(30, 365)),
                    defaults={
                        'score': random.randint(65, 98),
                        'commentaires': random.choice([
                            "Excellent travail, dépasse les attentes.",
                            "Résultats solides, très bonne intégration dans l'équipe.",
                            "Bonne performance globale, à encourager sur la prise d'initiative.",
                            "Compétences techniques très appréciées.",
                            "Continuez vos efforts, progression constante constatée."
                        ])
                    }
                )

            # 2. Ajouter des inscriptions aux formations
            num_form = random.randint(1, 2)
            selected_formations = random.sample(formations, num_form)
            for f in selected_formations:
                InscriptionFormation.objects.get_or_create(
                    employe=emp,
                    formation=f,
                    defaults={
                        'statut': random.choice(['Inscrit', 'En cours', 'Terminé']),
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Données de test générées avec succès pour {employes.count()} employés."))
