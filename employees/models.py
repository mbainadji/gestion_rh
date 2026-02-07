from django.db import models
from django.contrib.auth.models import User

class Departement(models.Model):
    nom = models.CharField(max_length=100, verbose_name="Nom du département")
    code = models.CharField(max_length=10, unique=True, verbose_name="Code")
    chef_de_service = models.OneToOneField('Employe', on_delete=models.SET_NULL, null=True, blank=True, related_name='departement_dirige', verbose_name="Chef de service")

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Département"

class Poste(models.Model):
    titre = models.CharField(max_length=100, verbose_name="Titre du poste")
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='postes', verbose_name="Département")
    responsabilites = models.TextField(blank=True, verbose_name="Responsabilités")
    missions = models.TextField(blank=True, verbose_name="Missions")

    def __str__(self):
        return f"{self.titre} ({self.departement.nom})"

    class Meta:
        verbose_name = "Poste"

class Employe(models.Model):
    ROLES = [
        ('ADMIN', 'Super Admin'),
        ('RH', 'Responsable RH'),
        ('MANAGER', 'Chef Service'),
        ('EMPLOYE', 'Employé'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profil', verbose_name="Utilisateur")
    role = models.CharField(max_length=20, choices=ROLES, default='EMPLOYE', verbose_name="Rôle")
    matricule = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Matricule")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    email = models.EmailField(unique=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='employes', verbose_name="Poste")
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    salaire = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire")

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.matricule})"

    @property
    def is_rh(self):
        return self.role == 'RH' or self.user.is_superuser or self.role == 'ADMIN'

    @property
    def is_manager(self):
        return self.role == 'MANAGER' or self.is_rh

    @property
    def is_only_employe(self):
        return self.role == 'EMPLOYE'

    @property
    def age(self):
        if self.date_naissance:
            import datetime
            today = datetime.date.today()
            return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        return None

    @property
    def age_a_venir(self):
        age = self.age
        return age + 1 if age is not None else None

    class Meta:
        verbose_name = "Employé"

class TypeContrat(models.Model):
    nom = models.CharField(max_length=50, verbose_name="Nom du type de contrat")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Contrat(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='contrats', verbose_name="Employé")
    type_contrat = models.ForeignKey(TypeContrat, on_delete=models.CASCADE, verbose_name="Type de contrat")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    fichier = models.FileField(upload_to='contrats/', null=True, blank=True, verbose_name="Fichier du contrat")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return f"Contrat {self.type_contrat} - {self.employe}"

class Conge(models.Model):
    TYPE_CONGE = [
        ('ANNUEL', 'Congé Annuel'),
        ('MALADIE', 'Congé Maladie'),
        ('MATERNITE', 'Maternité'),
        ('SANS_SOLDE', 'Sans Solde'),
        ('AUTRE', 'Autre'),
    ]
    STATUT_CONGE = [
        ('EN_ATTENTE', 'En attente'),
        ('APPROUVE', 'Approuvé'),
        ('REJETE', 'Rejeté'),
    ]
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='conges', verbose_name="Employé")
    validateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name='conges_a_valider', verbose_name="À l'attention de (Manager)")
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE, verbose_name="Type de congé")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(max_length=20, choices=STATUT_CONGE, default='EN_ATTENTE', verbose_name="Statut")
    motif = models.TextField(blank=True, verbose_name="Motif")
    commentaire_manager = models.TextField(blank=True, verbose_name="Commentaire Manager")

    def __str__(self):
        return f"{self.type_conge} - {self.employe} ({self.date_debut} au {self.date_fin})"

class Absence(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='absences', verbose_name="Employé")
    date = models.DateField(verbose_name="Date")
    motif = models.TextField(verbose_name="Motif")
    justifie = models.BooleanField(default=False, verbose_name="Justifié")

    def __str__(self):
        return f"Absence {self.employe} le {self.date}"

class Presence(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='presences', verbose_name="Employé")
    date = models.DateField(verbose_name="Date")
    heure_arrivee = models.TimeField(verbose_name="Heure d'arrivée")
    heure_depart = models.TimeField(null=True, blank=True, verbose_name="Heure de départ")
    heures_sup = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="Heures supplémentaires")

    def __str__(self):
        return f"Présence {self.employe} le {self.date}"

class FichePaie(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='fiches_paie', verbose_name="Employé")
    mois = models.IntegerField(verbose_name="Mois")
    annee = models.IntegerField(verbose_name="Année")
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire de base")
    primes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Primes")
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Déductions")
    net_a_payer = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net à payer")
    date_paiement = models.DateField(auto_now_add=True, verbose_name="Date de paiement")
    fichier_pdf = models.FileField(upload_to='fiches_paie/', null=True, blank=True, verbose_name="Fiche de paie PDF")

    def __str__(self):
        return f"Fiche de paie {self.mois}/{self.annee} - {self.employe}"

class Prime(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='primes_recues', verbose_name="Employé")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    motif = models.CharField(max_length=200, verbose_name="Motif")
    date = models.DateField(verbose_name="Date")

    def __str__(self):
        return f"Prime {self.montant} - {self.employe}"

class Evaluation(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='evaluations', verbose_name="Employé")
    evaluateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name='evaluations_donnees', verbose_name="Évaluateur")
    date = models.DateField(verbose_name="Date d'évaluation")
    score = models.IntegerField(verbose_name="Score / 100")
    commentaires = models.TextField(blank=True, verbose_name="Commentaires")

    def __str__(self):
        return f"Évaluation {self.employe} - {self.date}"

class Objectif(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='objectifs', verbose_name="Employé")
    description = models.TextField(verbose_name="Description")
    date_limite = models.DateField(verbose_name="Date limite")
    realise = models.BooleanField(default=False, verbose_name="Réalisé")

    def __str__(self):
        return f"Objectif {self.employe} - {self.date_limite}"

class Formation(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre de la formation")
    description = models.TextField(verbose_name="Description")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Budget")

    def __str__(self):
        return self.titre

class InscriptionFormation(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='formations', verbose_name="Employé")
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, verbose_name="Formation")
    statut = models.CharField(max_length=50, default='Inscrit', verbose_name="Statut")
    attestation = models.FileField(upload_to='attestations/', null=True, blank=True, verbose_name="Attestation")

    def __str__(self):
        return f"{self.employe} - {self.formation}"

class OffreEmploi(models.Model):
    titre = models.CharField(max_length=200, verbose_name="Titre de l'offre")
    description = models.TextField(verbose_name="Description")
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, verbose_name="Département")
    date_publication = models.DateField(auto_now_add=True, verbose_name="Date de publication")
    cloturee = models.BooleanField(default=False, verbose_name="Clôturée")

    def __str__(self):
        return self.titre

class Candidature(models.Model):
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name='candidatures', verbose_name="Offre")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(verbose_name="Email")
    cv = models.FileField(upload_to='cvs/', verbose_name="CV")
    lettre_motivation = models.TextField(blank=True, verbose_name="Lettre de motivation")
    statut = models.CharField(max_length=50, default='Nouveau', verbose_name="Statut")

    def __str__(self):
        return f"Candidature {self.prenom} {self.nom} pour {self.offre}"

class DocumentRH(models.Model):
    TYPE_DOC = [
        ('CONTRAT', 'Contrat'),
        ('CERTIFICAT', 'Certificat'),
        ('CV', 'CV'),
        ('PIECE_IDENTITE', 'Pièce d\'identité'),
        ('AUTRE', 'Autre'),
    ]
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='documents', verbose_name="Employé")
    titre = models.CharField(max_length=200, verbose_name="Titre du document")
    fichier = models.FileField(upload_to='documents_rh/', verbose_name="Fichier")
    type_doc = models.CharField(max_length=20, choices=TYPE_DOC, verbose_name="Type de document")
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    def __str__(self):
        return f"{self.titre} - {self.employe}"
