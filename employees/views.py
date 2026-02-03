from django.shortcuts import render, get_object_or_404, redirect
from .models import (
    Employe, Departement, Poste, Conge, Absence, Presence, 
    FichePaie, Prime, Evaluation, Objectif, Formation, 
    InscriptionFormation, OffreEmploi, Candidature, DocumentRH, TypeContrat
)
from .forms import (
    EmployeForm, DepartementForm, PosteForm, CongeForm, AbsenceForm,
    PresenceForm, FichePaieForm, EvaluationForm, FormationForm,
    OffreEmploiForm, CandidatureForm, DocumentRHForm
)
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def dashboard(request):
    total_employees = Employe.objects.count()
    departements = Departement.objects.annotate(num_employees=Count('postes__employes'))
    recent_conges = Conge.objects.filter(statut='EN_ATTENTE').order_by('-date_debut')[:5]
    context = {
        'total_employees': total_employees,
        'departements': departements,
        'recent_conges': recent_conges,
    }
    return render(request, 'employees/dashboard.html', context)

# Gestion des Employés
@login_required
def employee_list(request):
    query = request.GET.get('q')
    if query:
        employees = Employe.objects.filter(
            Q(nom__icontains=query) | 
            Q(prenom__icontains=query) | 
            Q(matricule__icontains=query) |
            Q(poste__titre__icontains=query)
        ).select_related('poste', 'poste__departement')
    else:
        employees = Employe.objects.all().select_related('poste', 'poste__departement')
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employe.objects.select_related('poste', 'poste__departement'), pk=pk)
    documents = DocumentRH.objects.filter(employe=employee)
    evaluations = Evaluation.objects.filter(employe=employee)
    contrats = employee.contrats.all()
    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'documents': documents,
        'evaluations': evaluations,
        'contrats': contrats,
    })

@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employé ajouté avec succès.")
            return redirect('employees:employee_list')
    else:
        form = EmployeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Ajouter un employé"})

@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employe, pk=pk)
    if request.method == 'POST':
        form = EmployeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Informations de l'employé mises à jour.")
            return redirect('employees:employee_detail', pk=pk)
    else:
        form = EmployeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier l'employé"})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employe, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, "Employé supprimé.")
        return redirect('employees:employee_list')
    return render(request, 'employees/confirm_delete.html', {'object': employee})

# Gestion des Départements
@login_required
def departement_list(request):
    departements = Departement.objects.annotate(num_employees=Count('postes__employes'))
    return render(request, 'employees/departement_list.html', {'departements': departements})

@login_required
def departement_detail(request, pk):
    departement = get_object_or_404(Departement.objects.annotate(num_employees=Count('postes__employes')), pk=pk)
    postes = departement.postes.annotate(num_employees=Count('employes'))
    return render(request, 'employees/departement_detail.html', {
        'departement': departement,
        'postes': postes,
    })

@login_required
def departement_create(request):
    if request.method == 'POST':
        form = DepartementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Département créé avec succès.")
            return redirect('employees:departement_list')
    else:
        form = DepartementForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Créer un département"})

@login_required
def departement_update(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    if request.method == 'POST':
        form = DepartementForm(request.POST, instance=departement)
        if form.is_valid():
            form.save()
            messages.success(request, "Département mis à jour.")
            return redirect('employees:departement_list')
    else:
        form = DepartementForm(instance=departement)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier le département"})

@login_required
def departement_delete(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    if request.method == 'POST':
        departement.delete()
        messages.success(request, "Département supprimé.")
        return redirect('employees:departement_list')
    return render(request, 'employees/confirm_delete.html', {'object': departement})

# Gestion des Postes
@login_required
def poste_list(request):
    postes = Poste.objects.select_related('departement').annotate(num_employees=Count('employes'))
    return render(request, 'employees/poste_list.html', {'postes': postes})

@login_required
def poste_create(request):
    if request.method == 'POST':
        form = PosteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:poste_list')
    else:
        form = PosteForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Créer un poste"})

# Gestion des Congés
@login_required
def conge_list(request):
    conges = Conge.objects.all().select_related('employe')
    return render(request, 'employees/conge_list.html', {'conges': conges})

from django.core.mail import send_mail
from django.conf import settings

@login_required
def conge_request(request):
    if request.method == 'POST':
        form = CongeForm(request.POST)
        if form.is_valid():
            conge = form.save()
            # Notification au manager
            if conge.validateur and conge.validateur.email:
                subject = f"Nouvelle demande de congé : {conge.employe}"
                message = f"Bonjour {conge.validateur.prenom},\n\nUne nouvelle demande de congé a été soumise par {conge.employe}.\nDu : {conge.date_debut}\nAu : {conge.date_fin}\nMotif : {conge.motif}\n\nMerci de vous connecter pour valider ou rejeter cette demande."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [conge.validateur.email])
            messages.success(request, "Demande de congé soumise et manager notifié.")
            return redirect('employees:conge_list')
    else:
        initial = {}
        if hasattr(request.user, 'profil'):
            initial['employe'] = request.user.profil
        form = CongeForm(initial=initial)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Demande de congé"})

@login_required
def conge_approve(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    conge.statut = 'APPROUVE'
    conge.save()
    # Notification à l'employé
    if conge.employe.email:
        subject = "Votre demande de congé a été APPROUVÉE"
        message = f"Bonjour {conge.employe.prenom},\n\nVotre demande de congé du {conge.date_debut} au {conge.date_fin} a été approuvée par {request.user.username}."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [conge.employe.email])
    messages.success(request, "Demande approuvée.")
    return redirect('employees:conge_list')

@login_required
def conge_reject(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    conge.statut = 'REJETE'
    conge.save()
    # Notification à l'employé
    if conge.employe.email:
        subject = "Votre demande de congé a été REJETÉE"
        message = f"Bonjour {conge.employe.prenom},\n\nVotre demande de congé du {conge.date_debut} au {conge.date_fin} a été rejetée."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [conge.employe.email])
    messages.warning(request, "Demande rejetée.")
    return redirect('employees:conge_list')

# Gestion des Présences
@login_required
def presence_list(request):
    presences = Presence.objects.all().select_related('employe').order_by('-date')
    return render(request, 'employees/presence_list.html', {'presences': presences})

@login_required
def presence_create(request):
    departements = Departement.objects.all()
    selected_dept = request.GET.get('departement')
    
    employees = []
    if selected_dept:
        employees = Employe.objects.filter(poste__departement_id=selected_dept)

    if request.method == 'POST':
        date = request.POST.get('date')
        emp_ids = request.POST.getlist('employees')
        h_arrivee = request.POST.get('heure_arrivee', '08:00')
        h_depart = request.POST.get('heure_depart', '17:00')
        
        for emp_id in emp_ids:
            Presence.objects.create(
                employe_id=emp_id,
                date=date,
                heure_arrivee=h_arrivee,
                heure_depart=h_depart
            )
        messages.success(request, f"Présences enregistrées pour {len(emp_ids)} employés.")
        return redirect('employees:presence_list')

    return render(request, 'employees/presence_form.html', {
        'departements': departements,
        'employees': employees,
        'selected_dept': selected_dept,
    })

# Gestion de la Paie
@login_required
def paie_list(request):
    fiches = FichePaie.objects.all().select_related('employe').order_by('-annee', '-mois')
    return render(request, 'employees/paie_list.html', {'fiches': fiches})

@login_required
def paie_create(request):
    if request.method == 'POST':
        form = FichePaieForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:paie_list')
    else:
        form = FichePaieForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Générer une fiche de paie"})

# Gestion des Formations
@login_required
def formation_list(request):
    formations = Formation.objects.all()
    return render(request, 'employees/formation_list.html', {'formations': formations})

@login_required
def formation_create(request):
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:formation_list')
    else:
        form = FormationForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Créer une formation"})

# Recrutements
@login_required
def recrutement_list(request):
    offres = OffreEmploi.objects.all().annotate(num_candidatures=Count('candidatures'))
    return render(request, 'employees/recrutement_list.html', {'offres': offres})

@login_required
def recrutement_create(request):
    if request.method == 'POST':
        form = OffreEmploiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees:recrutement_list')
    else:
        form = OffreEmploiForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Publier une offre"})

# Intégrations / Export
import csv
from django.http import HttpResponse

@login_required
def export_employees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Matricule', 'Nom', 'Prénom', 'Email', 'Poste', 'Département', 'Date Embauche', 'Salaire'])
    
    employees = Employe.objects.all().select_related('poste', 'poste__departement')
    for e in employees:
        writer.writerow([e.matricule, e.nom, e.prenom, e.email, e.poste.titre, e.poste.departement.nom, e.date_embauche, e.salaire])
        
    return response

# Politiques RH
@login_required
def politique_list(request):
    types_contrat = TypeContrat.objects.all()
    return render(request, 'employees/politique_list.html', {'types_contrat': types_contrat})

@login_required
def politique_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        if nom:
            TypeContrat.objects.create(nom=nom, description=description)
            return redirect('employees:politique_list')
    return render(request, 'employees/politique_form.html', {'title': "Ajouter un type de contrat"})
