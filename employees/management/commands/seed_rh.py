from django.core.management.base import BaseCommand
from employees.models import Departement, Poste, Employe
from datetime import date

class Command(BaseCommand):
    help = 'Seeds the database with demo data'

    def handle(self, *args, **options):
        # Clear existing data
        Employe.objects.all().delete()
        Poste.objects.all().delete()
        Departement.objects.all().delete()

        d1 = Departement.objects.create(nom="Ressources Humaines", code="RH")
        d2 = Departement.objects.create(nom="Informatique", code="IT")
        d3 = Departement.objects.create(nom="Marketing", code="MKT")

        p1 = Poste.objects.create(titre="DRH", departement=d1)
        p2 = Poste.objects.create(titre="Développeur Senior", departement=d2)
        p3 = Poste.objects.create(titre="Chef de Produit", departement=d3)

        Employe.objects.create(nom="Martin", prenom="Alice", email="alice.martin@example.com", telephone="0123456789", date_embauche=date(2020, 1, 15), poste=p1, salaire=5000)
        Employe.objects.create(nom="Bernard", prenom="Bob", email="bob.bernard@example.com", telephone="0987654321", date_embauche=date(2021, 5, 20), poste=p2, salaire=4500)
        Employe.objects.create(nom="Petit", prenom="Charlie", email="charlie.petit@example.com", date_embauche=date(2022, 10, 10), poste=p3, salaire=4000)

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data'))
