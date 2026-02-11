from django import forms
from .models import (
    Employe, Departement, Poste, Conge, Absence, Presence, 
    FichePaie, Prime, Evaluation, Objectif, Formation, 
    InscriptionFormation, OffreEmploi, Candidature, DocumentRH
)

class EmployeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, label="Mot de passe (laisser vide pour ne pas changer)")
    leads_departement = forms.ModelChoiceField(queryset=Departement.objects.all(), required=False, label="Dirige le département (pour les Chefs de Service)")

    class Meta:
        model = Employe
        exclude = ['user']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            self.fields['password'].label = "Mot de passe"
            self.fields['password'].help_text = "Laisser vide pour utiliser le mot de passe par défaut (departement123 pour les chefs, password123 pour les employés)"
        
        # Filtre pour les managers (Chefs de Département)
        if self.user and not self.user.is_superuser:
            if hasattr(self.user, 'profil'):
                profil = self.user.profil
                if not profil.is_rh and profil.is_manager:
                    # Restreindre les postes au département du manager
                    if profil.poste:
                        self.fields['poste'].queryset = Poste.objects.filter(departement=profil.poste.departement)
                        self.fields['leads_departement'].queryset = Departement.objects.filter(id=profil.poste.departement.id)
                    
                    # Un manager ne peut créer que des simples employés par défaut
                    self.fields['role'].choices = [('EMPLOYE', 'Employé')]
                    self.fields['role'].initial = 'EMPLOYE'

        if self.instance and self.instance.pk:
            try:
                self.fields['leads_departement'].initial = self.instance.departement_dirige
            except:
                pass

    def save(self, commit=True):
        from django.contrib.auth.models import User
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if not instance.pk:  # Création
            # Créer un utilisateur associé
            username = instance.email.split('@')[0]
            # S'assurer que le username est unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            default_password = "password123"
            if instance.role == 'MANAGER':
                default_password = "departement123"
                
            user = User.objects.create_user(
                username=username,
                email=instance.email,
                password=password if password else default_password
            )
            instance.user = user
        elif password or 'email' in self.changed_data:  # Mise à jour
            if instance.user:
                if password:
                    instance.user.set_password(password)
                if 'email' in self.changed_data:
                    instance.user.email = instance.email
                instance.user.save()
        
        if commit:
            instance.save()
            # Gérer le département dirigé
            leads_dept = self.cleaned_data.get('leads_departement')
            if instance.role == 'MANAGER' and leads_dept:
                # Si cet employé doit diriger un département
                leads_dept.chef_de_service = instance
                leads_dept.save()
            elif instance.role != 'MANAGER':
                # Si l'employé n'est plus manager, il ne doit plus diriger de département
                Departement.objects.filter(chef_de_service=instance).update(chef_de_service=None)
                
        return instance

class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chef_de_service'].queryset = Employe.objects.filter(role='MANAGER')

class PosteForm(forms.ModelForm):
    class Meta:
        model = Poste
        fields = '__all__'

class CongeForm(forms.ModelForm):
    class Meta:
        model = Conge
        fields = ['employe', 'validateur', 'type_conge', 'date_debut', 'date_fin', 'motif']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'profil'):
            profil = user.profil
            if profil.role == 'MANAGER':
                # Si c'est un manager, il ne peut choisir que des RH comme validateurs
                self.fields['validateur'].queryset = Employe.objects.filter(role='RH')
            elif profil.role == 'EMPLOYE':
                # Si c'est un employé, il peut choisir des Managers ou RH
                self.fields['validateur'].queryset = Employe.objects.filter(role__in=['MANAGER', 'RH'])

class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class PresenceForm(forms.ModelForm):
    class Meta:
        model = Presence
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'type': 'time'}),
            'heure_depart': forms.TimeInput(attrs={'type': 'time'}),
        }

class FichePaieForm(forms.ModelForm):
    class Meta:
        model = FichePaie
        fields = [
            'employe',
            'mois',
            'annee',
            'salaire_base',
            'primes',
            'deductions',
            'net_a_payer',
        ]

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = '__all__'
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }

class InscriptionFormationUpdateForm(forms.ModelForm):
    class Meta:
        model = InscriptionFormation
        fields = ['statut', 'attestation']

class OffreEmploiForm(forms.ModelForm):
    class Meta:
        model = OffreEmploi
        fields = '__all__'

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['offre', 'nom', 'prenom', 'email', 'cv', 'lettre_motivation']

class DocumentRHForm(forms.ModelForm):
    class Meta:
        model = DocumentRH
        fields = ['titre', 'fichier', 'type_doc']
