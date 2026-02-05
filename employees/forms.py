from django import forms
from .models import (
    Employe, Departement, Poste, Conge, Absence, Presence, 
    FichePaie, Prime, Evaluation, Objectif, Formation, 
    InscriptionFormation, OffreEmploi, Candidature, DocumentRH
)

class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = '__all__'
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date'}),
        }

class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = '__all__'

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
        fields = '__all__'

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
