from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from employees.models import (
    Departement, Poste, Employe, TypeContrat, Contrat, 
    Conge, Absence, Presence, FichePaie, Prime, 
    Evaluation, Objectif, Formation, InscriptionFormation, 
    OffreEmploi, Candidature, DocumentRH
)
from datetime import date, timedelta, time
import random
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds the database with comprehensive demo data'

    def handle(self, *args, **options):
        self.stdout.write('Deleting existing data...')
        # Clear existing data in correct order to avoid FK issues
        Candidature.objects.all().delete()
        OffreEmploi.objects.all().delete()
        InscriptionFormation.objects.all().delete()
        Formation.objects.all().delete()
        Objectif.objects.all().delete()
        Evaluation.objects.all().delete()
        Prime.objects.all().delete()
        FichePaie.objects.all().delete()
        Presence.objects.all().delete()
        Absence.objects.all().delete()
        Conge.objects.all().delete()
        Contrat.objects.all().delete()
        TypeContrat.objects.all().delete()
        DocumentRH.objects.all().delete()
        Employe.objects.all().delete()
        Poste.objects.all().delete()
        Departement.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating Departments...')
        deps_data = [
            ("Direction Générale", "DG"),
            ("Ressources Humaines", "RH"),
            ("Informatique", "IT"),
            ("Marketing & Communication", "MKT"),
            ("Finance & Comptabilité", "FIN"),
            ("Ventes", "SALES"),
            ("Production", "PROD"),
        ]
        deps = {}
        for nom, code in deps_data:
            deps[code] = Departement.objects.create(nom=nom, code=code)

        self.stdout.write('Creating Positions...')
        postes_data = [
            ("Directeur Général", "DG", "Gestion globale de l'entreprise", "Définir la stratégie"),
            ("Responsable RH", "RH", "Gestion du personnel", "Recrutement, paie"),
            ("Chargé de Recrutement", "RH", "Sourcing de candidats", "Entretiens"),
            ("CTO", "IT", "Direction technique", "Architecture logicielle"),
            ("Développeur Senior", "IT", "Développement fullstack", "Code review, mentorat"),
            ("Développeur Junior", "IT", "Maintenance et petites features", "Apprentissage"),
            ("Responsable Marketing", "MKT", "Stratégie marketing", "Campagnes pub"),
            ("Community Manager", "MKT", "Gestion réseaux sociaux", "Engagement clients"),
            ("Directeur Financier", "FIN", "Gestion budget", "Reporting financier"),
            ("Comptable", "FIN", "Tenue des comptes", "Facturation"),
            ("Responsable Commercial", "SALES", "Développement des ventes", "Prospection"),
            ("Commercial", "SALES", "Vente de produits", "Closing"),
        ]
        postes = []
        for titre, dep_code, resp, missions in postes_data:
            postes.append(Poste.objects.create(
                titre=titre, 
                departement=deps[dep_code],
                responsabilites=resp,
                missions=missions
            ))

        self.stdout.write('Creating TypeContrat...')
        tc_cdi = TypeContrat.objects.create(nom="CDI", description="Contrat à Durée Indéterminée")
        tc_cdd = TypeContrat.objects.create(nom="CDD", description="Contrat à Durée Déterminée")
        tc_stage = TypeContrat.objects.create(nom="Stage", description="Stage de fin d'études")
        type_contrats = [tc_cdi, tc_cdd, tc_stage]

        self.stdout.write('Creating Employees...')
        noms = ["Dupont", "Durand", "Lefebvre", "Moreau", "Simon", "Laurent", "Michel", "Garcia", "Thomas", "Robert"]
        prenoms = ["Jean", "Marie", "Pierre", "Anne", "Thomas", "Lucie", "Nicolas", "Sarah", "Antoine", "Julie"]
        
        employes = []
        for i in range(15):
            nom = random.choice(noms)
            prenom = random.choice(prenoms)
            username = f"{prenom.lower()}.{nom.lower()}{i}"
            email = f"{username}@example.com"
            
            user = User.objects.create_user(username=username, email=email, password='password123')
            
            emp = Employe.objects.create(
                user=user,
                matricule=f"EMP{1000+i}",
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=f"06{random.randint(10000000, 99999999)}",
                adresse=f"{random.randint(1, 100)} Rue de la Paix, Paris",
                poste=random.choice(postes),
                date_embauche=date(2020, 1, 1) + timedelta(days=random.randint(0, 1000)),
                salaire=Decimal(random.randint(2500, 7000)),
                date_naissance=date(1980, 1, 1) + timedelta(days=random.randint(0, 7000))
            )
            employes.append(emp)

            # Create Contract for each employee
            Contrat.objects.create(
                employe=emp,
                type_contrat=random.choice(type_contrats),
                date_debut=emp.date_embauche,
                actif=True
            )

        self.stdout.write('Creating Leaves and Absences...')
        for emp in employes[:10]:
            # Conge
            Conge.objects.create(
                employe=emp,
                type_conge=random.choice(['ANNUEL', 'MALADIE', 'AUTRE']),
                date_debut=date(2024, 1, 1) + timedelta(days=random.randint(0, 30)),
                date_fin=date(2024, 1, 1) + timedelta(days=random.randint(31, 40)),
                statut=random.choice(['APPROUVE', 'EN_ATTENTE']),
                motif="Vacances" if random.random() > 0.5 else "Raison personnelle"
            )
            # Absence
            Absence.objects.create(
                employe=emp,
                date=date(2024, 2, random.randint(1, 28)),
                motif="Retard train" if random.random() > 0.5 else "Rendez-vous médical",
                justifie=random.choice([True, False])
            )

        self.stdout.write('Creating Presence data...')
        for emp in employes[:5]:
            for d in range(1, 10):
                Presence.objects.create(
                    employe=emp,
                    date=date(2024, 3, d),
                    heure_arrivee=time(8, random.randint(30, 59)),
                    heure_depart=time(17, random.randint(30, 59)),
                    heures_sup=Decimal(random.randint(0, 2))
                )

        self.stdout.write('Creating Payroll data...')
        for emp in employes[:5]:
            salaire_base = emp.salaire
            primes = Decimal(random.randint(100, 500))
            deductions = Decimal(random.randint(50, 200))
            FichePaie.objects.create(
                employe=emp,
                mois=1,
                annee=2024,
                salaire_base=salaire_base,
                primes=primes,
                deductions=deductions,
                net_a_payer=salaire_base + primes - deductions
            )

        self.stdout.write('Creating Formations...')
        f1 = Formation.objects.create(
            titre="Management Agile",
            description="Apprendre les bases du Scrum et Kanban",
            date_debut=date(2024, 4, 1),
            date_fin=date(2024, 4, 3),
            budget=Decimal(1500)
        )
        f2 = Formation.objects.create(
            titre="Python Avancé",
            description="Maîtriser les décorateurs et générateurs",
            date_debut=date(2024, 5, 1),
            date_fin=date(2024, 5, 5),
            budget=Decimal(2000)
        )

        for emp in employes[:4]:
            InscriptionFormation.objects.create(
                employe=emp,
                formation=random.choice([f1, f2]),
                statut="Inscrit"
            )

        self.stdout.write('Creating Job Offers and Applications...')
        offre = OffreEmploi.objects.create(
            titre="Développeur Python/Django",
            description="Nous recherchons un dev passionné...",
            departement=deps["IT"]
        )
        Candidature.objects.create(
            offre=offre,
            nom="Martin",
            prenom="Paul",
            email="paul.martin@test.com",
            lettre_motivation="Je suis très motivé !",
            statut="Nouveau"
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded comprehensive demo data'))
