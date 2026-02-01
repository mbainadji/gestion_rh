from django.test import TestCase
from django.urls import reverse
from .models import Departement, Poste, Employe
from datetime import date
from django.contrib.auth.models import User

class HRMTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.dept = Departement.objects.create(nom="RH", code="RH01")
        self.poste = Poste.objects.create(titre="Manager", departement=self.dept)
        self.employe = Employe.objects.create(
            nom="Dupont", prenom="Jean", email="jean.dupont@example.com",
            date_embauche=date.today(), poste=self.poste, salaire=3000
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('employees:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RH")
        self.assertContains(response, "1") # Total employees count in dashboard

    def test_employee_list_view(self):
        response = self.client.get(reverse('employees:employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dupont")

    def test_employee_detail_view(self):
        url = reverse('employees:employee_detail', args=[self.employe.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jean.dupont@example.com")
