from django.contrib import admin
from .models import (
    Departement, Poste, Employe, TypeContrat, Contrat, Conge, Absence, 
    Presence, FichePaie, Prime, Evaluation, Objectif, Formation, 
    InscriptionFormation, OffreEmploi, Candidature, DocumentRH
)

@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code')
    search_fields = ('nom', 'code')

@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'departement')
    list_filter = ('departement',)
    search_fields = ('titre',)

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'email', 'poste', 'date_embauche')
    list_filter = ('poste__departement', 'poste', 'date_embauche')
    search_fields = ('nom', 'prenom', 'email', 'matricule')

@admin.register(TypeContrat)
class TypeContratAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_contrat', 'date_debut', 'actif')
    list_filter = ('type_contrat', 'actif')

@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = ('employe', 'type_conge', 'date_debut', 'date_fin', 'statut')
    list_filter = ('type_conge', 'statut')

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('employe', 'date', 'justifie')
    list_filter = ('justifie',)

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('employe', 'date', 'heure_arrivee', 'heure_depart')
    list_filter = ('date',)

@admin.register(FichePaie)
class FichePaieAdmin(admin.ModelAdmin):
    list_display = ('employe', 'mois', 'annee', 'net_a_payer')
    list_filter = ('annee', 'mois')

@admin.register(Prime)
class PrimeAdmin(admin.ModelAdmin):
    list_display = ('employe', 'montant', 'date')

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('employe', 'evaluateur', 'date', 'score')

@admin.register(Objectif)
class ObjectifAdmin(admin.ModelAdmin):
    list_display = ('employe', 'date_limite', 'realise')
    list_filter = ('realise',)

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_debut', 'date_fin')

@admin.register(InscriptionFormation)
class InscriptionFormationAdmin(admin.ModelAdmin):
    list_display = ('employe', 'formation', 'statut')

@admin.register(OffreEmploi)
class OffreEmploiAdmin(admin.ModelAdmin):
    list_display = ('titre', 'departement', 'date_publication', 'cloturee')

@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ('offre', 'nom', 'prenom', 'statut')
    list_filter = ('statut',)

@admin.register(DocumentRH)
class DocumentRHAdmin(admin.ModelAdmin):
    list_display = ('titre', 'employe', 'type_doc', 'date_ajout')
    list_filter = ('type_doc',)
