from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import csv
from django.http import HttpResponse

from .models import (
    Employe, Departement, Poste, Conge, Absence, Presence, 
    FichePaie, Prime, Evaluation, Objectif, Formation, 
    InscriptionFormation, OffreEmploi, Candidature, DocumentRH, TypeContrat
)
from .forms import (
    EmployeForm, DepartementForm, PosteForm, CongeForm, AbsenceForm,
    PresenceForm, FichePaieForm, EvaluationForm, FormationForm,
    OffreEmploiForm, CandidatureForm, DocumentRHForm,
    InscriptionFormationUpdateForm
)

from .decorators import rh_required, manager_required, superadmin_required, dept_admin_required

@login_required
def dashboard(request):
    today = timezone.now().date()
    if not hasattr(request.user, 'profil') or request.user.is_superuser or request.user.profil.is_superadmin:
        # Cas du superuser ou profil ADMIN (voit tout au niveau global)
        total_employees = Employe.objects.count()
        departements = Departement.objects.annotate(num_employees=Count('postes__employes'))
        recent_conges = Conge.objects.filter(statut='EN_ATTENTE').order_by('-date_debut')[:5]
        total_pending_conges = Conge.objects.filter(statut='EN_ATTENTE').count()
        anniversaires = Employe.objects.filter(date_naissance__month=today.month).order_by('date_naissance__day')
    else:
        profil = request.user.profil
        if profil.is_rh:
            total_employees = Employe.objects.count()
            departements = Departement.objects.annotate(num_employees=Count('postes__employes'))
            recent_conges = Conge.objects.filter(statut='EN_ATTENTE').order_by('-date_debut')[:5]
            total_pending_conges = Conge.objects.filter(statut='EN_ATTENTE').count()
            anniversaires = Employe.objects.filter(date_naissance__month=today.month).order_by('date_naissance__day')
        elif profil.is_dept_admin or profil.role == 'EMPLOYE':
            if profil.poste:
                dept = profil.poste.departement
                total_employees = Employe.objects.filter(poste__departement=dept).count()
                departements = Departement.objects.filter(id=dept.id).annotate(num_employees=Count('postes__employes'))
                
                if profil.is_dept_admin:
                    recent_conges = Conge.objects.filter(employe__poste__departement=dept, statut='EN_ATTENTE').order_by('-date_debut')[:5]
                    total_pending_conges = Conge.objects.filter(employe__poste__departement=dept, statut='EN_ATTENTE').count()
                else:
                    recent_conges = Conge.objects.filter(employe=profil).order_by('-date_debut')[:5]
                    total_pending_conges = Conge.objects.filter(employe=profil, statut='EN_ATTENTE').count()
                
                anniversaires = Employe.objects.filter(poste__departement=dept, date_naissance__month=today.month).order_by('date_naissance__day')
            else:
                total_employees = 0
                departements = Departement.objects.none()
                recent_conges = []
                total_pending_conges = 0
                anniversaires = []

    # Logique commune pour les formations
    if request.user.is_superuser or (hasattr(request.user, 'profil') and request.user.profil.is_rh):
        total_formations = Formation.objects.count()
    else:
        profil = request.user.profil
        if profil.poste:
            total_formations = Formation.objects.filter(Q(departement=profil.poste.departement) | Q(departement__isnull=True)).count()
        else:
            total_formations = Formation.objects.filter(departement__isnull=True).count()

    last_7_days = [(today - timezone.timedelta(days=i)) for i in range(6, -1, -1)]
    arrivals_per_day = []
    
    # Filtrer les arrivées si manager
    base_employees = Employe.objects.all()
    if hasattr(request.user, 'profil') and request.user.profil.is_manager and not request.user.profil.is_rh:
        if request.user.profil.poste:
            base_employees = base_employees.filter(poste__departement=request.user.profil.poste.departement)
        else:
            base_employees = base_employees.none()

    for day in last_7_days:
        count = base_employees.filter(date_embauche=day).count()
        arrivals_per_day.append({
            'day': day.strftime('%a'),
            'count': count
        })

    context = {
        'total_employees': total_employees,
        'departements': departements,
        'total_formations': total_formations,
        'recent_conges': recent_conges,
        'total_pending_conges': total_pending_conges,
        'anniversaires': anniversaires if 'anniversaires' in locals() else [],
        'arrivals_per_day': arrivals_per_day,
    }
    return render(request, 'employees/dashboard.html', context)

# Gestion des Employés
@login_required
def employee_list(request):
    query = request.GET.get('q')
    
    employees = Employe.objects.all().select_related('poste', 'poste__departement')
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if profil.is_dept_admin:
            # Chef de service : restreint à son département
            if profil.poste:
                employees = employees.filter(poste__departement=profil.poste.departement)
            else:
                employees = employees.none()
        elif not profil.is_superadmin and not profil.is_rh:
            # Simple employé ne voit que les talents de son département (nouveau critère)
            if profil.poste:
                employees = employees.filter(poste__departement=profil.poste.departement)
            else:
                employees = employees.none()

    if query:
        employees = employees.filter(
            Q(nom__icontains=query) | 
            Q(prenom__icontains=query) | 
            Q(matricule__icontains=query) |
            Q(poste__titre__icontains=query)
        )
    
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employe.objects.select_related('poste', 'poste__departement'), pk=pk)
    
    if not request.user.is_superuser:
        profil = request.user.profil
        # Restriction : 
        # SuperAdmin voit tout
        # DeptAdmin voit son département
        # Employé ne voit que lui-même
        if not profil.is_superadmin and not profil.is_rh:
            if profil.is_dept_admin:
                if not profil.poste or not employee.poste or employee.poste.departement != profil.poste.departement:
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied
            else:
                if employee != profil:
                    # Un employé peut voir les talents de son département
                    if not profil.poste or not employee.poste or employee.poste.departement != profil.poste.departement:
                        from django.core.exceptions import PermissionDenied
                        raise PermissionDenied

    documents = DocumentRH.objects.filter(employe=employee)
    evaluations = Evaluation.objects.filter(employe=employee)
    contrats = employee.contrats.all()
    
    # Employé ne voit pas son propre salaire s'il n'a pas les droits ? 
    # Pour l'instant on laisse mais on pourra filtrer dans le template
    
    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'documents': documents,
        'evaluations': evaluations,
        'contrats': contrats,
    })

@login_required
@manager_required
def employee_create(request):
    # Tout manager (SuperAdmin ou DeptAdmin) peut créer
    initial_data = {}
    role_param = request.GET.get('role')
    dept_id = request.GET.get('dept_id')
    
    if role_param:
        initial_data['role'] = role_param
    if dept_id:
        initial_data['leads_departement'] = dept_id
        # Si on passe un dept_id, on suppose que c'est pour un manager de ce dept
        try:
            dept = Departement.objects.get(id=dept_id)
            # On peut aussi pré-remplir le poste si nécessaire
        except Departement.DoesNotExist:
            pass

    if request.method == 'POST':
        form = EmployeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Employé ajouté avec succès.")
            return redirect('employees:employee_list')
    else:
        form = EmployeForm(user=request.user, initial=initial_data)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Ajouter un employé"})

@login_required
@dept_admin_required
def employee_update(request, pk):
    employee = get_object_or_404(Employe, pk=pk)
    
    # Vérification des permissions pour les Dept Admins
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_superadmin:
            if employee.poste.departement != profil.poste.departement:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
                
    if request.method == 'POST':
        form = EmployeForm(request.POST, instance=employee, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Informations de l'employé mises à jour.")
            return redirect('employees:employee_detail', pk=pk)
    else:
        form = EmployeForm(instance=employee, user=request.user)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier l'employé"})

@login_required
@dept_admin_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employe, pk=pk)
    
    # Vérification des permissions pour les managers
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_superadmin:
            if employee.poste.departement != profil.poste.departement:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
                
    if request.method == 'POST':
        employee.delete()
        messages.success(request, "Employé supprimé.")
        return redirect('employees:employee_list')
    return render(request, 'employees/confirm_delete.html', {'object': employee})

@login_required
def document_create(request, employee_pk):
    employee = get_object_or_404(Employe, pk=employee_pk)
    
    # Vérification des permissions : RH, Manager du dept, ou l'employé lui-même
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh:
            if profil.is_manager:
                if employee.poste.departement != profil.poste.departement:
                    raise PermissionDenied
            else:
                # Simple employé : ne peut uploader que pour lui-même
                if employee != profil:
                    raise PermissionDenied

    if request.method == 'POST':
        form = DocumentRHForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employe = employee
            document.save()
            messages.success(request, "Document ajouté avec succès.")
            return redirect('employees:employee_detail', pk=employee_pk)
    else:
        form = DocumentRHForm(initial={'employe': employee})
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Ajouter un document"})

# Gestion des Départements
@login_required
def departement_list(request):
    departements = Departement.objects.annotate(num_employees=Count('postes__employes'))
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            # Employé et Manager de département : ne voient que leur département
            if hasattr(profil, 'leads_departement') and profil.leads_departement:
                departements = departements.filter(id=profil.leads_departement.id)
            elif profil.poste:
                departements = departements.filter(id=profil.poste.departement.id)
            else:
                departements = departements.none()

    return render(request, 'employees/departement_list.html', {'departements': departements})

@login_required
def departement_detail(request, pk):
    departement = get_object_or_404(Departement.objects.annotate(num_employees=Count('postes__employes')), pk=pk)
    
    # Restriction
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if hasattr(profil, 'leads_departement') and profil.leads_departement and departement != profil.leads_departement:
                # Si c'est un manager, il doit être le manager de CE département
                # Mais attendez, un employé peut voir les détails de son propre département aussi ?
                # "verra l'effectif selon son departement tout les informations concernat son departement"
                # Donc on autorise si c'est son département.
                pass 
            
            # Vérification finale : est-ce son département ?
            user_dept = None
            if profil.poste:
                user_dept = profil.poste.departement
            elif hasattr(profil, 'leads_departement') and profil.leads_departement:
                user_dept = profil.leads_departement
                
            if departement != user_dept:
                raise PermissionDenied

    postes = departement.postes.annotate(num_employees=Count('employes'))
    return render(request, 'employees/departement_detail.html', {
        'departement': departement,
        'postes': postes,
    })

@login_required
@superadmin_required
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
@manager_required
def departement_update(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    
    # Restriction
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if profil.leads_departement and departement != profil.leads_departement:
                raise PermissionDenied
            elif profil.poste and departement != profil.poste.departement:
                raise PermissionDenied

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
@superadmin_required
def departement_delete(request, pk):
    departement = get_object_or_404(Departement, pk=pk)
    if request.method == 'POST':
        departement.delete()
        messages.success(request, "Département supprimé.")
        return redirect('employees:departement_list')
    return render(request, 'employees/confirm_delete.html', {'object': departement})

# Gestion des Postes
@login_required
@rh_required
@login_required
def poste_list(request):
    postes = Poste.objects.select_related('departement').annotate(num_employees=Count('employes'))
    return render(request, 'employees/poste_list.html', {'postes': postes})

@login_required
@rh_required
def poste_create(request):
    if request.method == 'POST':
        form = PosteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Poste créé avec succès.")
            return redirect('employees:poste_list')
    else:
        form = PosteForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Créer un poste"})

@login_required
@rh_required
def poste_detail(request, pk):
    poste = get_object_or_404(Poste.objects.select_related('departement').annotate(num_employees=Count('employes')), pk=pk)
    employees = poste.employes.all()
    return render(request, 'employees/poste_detail.html', {'poste': poste, 'employees': employees})

@login_required
@rh_required
def poste_update(request, pk):
    poste = get_object_or_404(Poste, pk=pk)
    if request.method == 'POST':
        form = PosteForm(request.POST, instance=poste)
        if form.is_valid():
            form.save()
            messages.success(request, "Poste mis à jour.")
            return redirect('employees:poste_list')
    else:
        form = PosteForm(instance=poste)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier le poste"})

@login_required
@rh_required
def poste_delete(request, pk):
    poste = get_object_or_404(Poste, pk=pk)
    if request.method == 'POST':
        poste.delete()
        messages.success(request, "Poste supprimé.")
        return redirect('employees:poste_list')
    return render(request, 'employees/confirm_delete.html', {'object': poste})

# Gestion des Congés
@login_required
def conge_list(request):
    if not hasattr(request.user, 'profil'):
        # Cas du superuser sans profil
        return render(request, 'employees/conge_list.html', {'conges': []})
        
    profil = request.user.profil
    if profil.is_superadmin:
        # Super admin ne gère pas les congés
        conges = []
    elif profil.is_rh:
        conges = Conge.objects.all().select_related('employe')
    elif profil.is_dept_admin:
        if profil.poste:
            conges = Conge.objects.filter(employe__poste__departement=profil.poste.departement).select_related('employe')
        else:
            conges = []
    else:
        conges = Conge.objects.filter(employe=profil).select_related('employe')
        
    return render(request, 'employees/conge_list.html', {'conges': conges})

from django.core.mail import send_mail
from django.conf import settings

@login_required
def conge_request(request):
    # Le superadmin n'a pas de profil pour demander un congé pour lui-même
    if request.user.is_superuser:
        messages.error(request, "Le superadmin ne peut pas soumettre de demande de congé pour lui-même.")
        return redirect('employees:conge_list')
        
    profil = request.user.profil
    if request.method == 'POST':
        form = CongeForm(request.POST, user=request.user)
        if form.is_valid():
            conge = form.save(commit=False)
            conge.employe = profil
            conge.save()
            # Notification au manager
            if conge.validateur and conge.validateur.email:
                subject = f"Nouvelle demande de congé : {conge.employe}"
                message = f"Bonjour {conge.validateur.prenom},\n\nUne nouvelle demande de congé a été soumise par {conge.employe}.\nDu : {conge.date_debut}\nAu : {conge.date_fin}\nMotif : {conge.motif}\n\nMerci de vous connecter pour valider ou rejeter cette demande."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [conge.validateur.email])
            messages.success(request, "Demande de congé soumise.")
            return redirect('employees:conge_list')
    else:
        initial = {'employe': profil}
        form = CongeForm(initial=initial, user=request.user)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Demande de congé"})

@login_required
@manager_required
def conge_approve(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh:
            if conge.employe.poste.departement != profil.poste.departement:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            # Un manager ne peut pas approuver la demande d'un autre manager
            if conge.employe.role == 'MANAGER':
                messages.error(request, "Seul un responsable RH peut approuver la demande d'un chef de service.")
                return redirect('employees:conge_list')

    conge.statut = 'APPROUVE'
    conge.save()
    # Notification à l'employé
    if conge.employe.email:
        subject = "Votre demande de congé a été APPROUVÉE"
        message = f"Bonjour {conge.employe.prenom},\n\nVotre demande de congé du {conge.date_debut} au {conge.date_fin} a été approuvée."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [conge.employe.email])
    messages.success(request, "Demande approuvée.")
    return redirect('employees:conge_list')

@login_required
@manager_required
def conge_reject(request, pk):
    conge = get_object_or_404(Conge, pk=pk)
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh:
            if conge.employe.poste.departement != profil.poste.departement:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            # Un manager ne peut pas rejeter la demande d'un autre manager
            if conge.employe.role == 'MANAGER':
                messages.error(request, "Seul un responsable RH peut rejeter la demande d'un chef de service.")
                return redirect('employees:conge_list')

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
    if request.user.is_superuser:
        presences = Presence.objects.all().select_related('employe').order_by('-date')
    else:
        profil = request.user.profil
        if profil.is_rh:
            presences = Presence.objects.all().select_related('employe').order_by('-date')
        elif profil.is_manager:
            presences = Presence.objects.filter(employe__poste__departement=profil.poste.departement).select_related('employe').order_by('-date')
        else:
            presences = Presence.objects.filter(employe=profil).select_related('employe').order_by('-date')
    return render(request, 'employees/presence_list.html', {'presences': presences})

@login_required
@manager_required
def presence_create(request):
    if request.user.is_superuser:
        departements = Departement.objects.all()
    else:
        profil = request.user.profil
        if profil.is_rh:
            departements = Departement.objects.all()
        else:
            departements = Departement.objects.filter(id=profil.poste.departement.id)
    
    selected_dept = request.GET.get('departement')
    
    employees = []
    if selected_dept:
        # Vérification sécurité pour le manager
        if not request.user.is_superuser:
            profil = request.user.profil
            if not profil.is_rh and int(selected_dept) != profil.poste.departement.id:
                raise PermissionDenied
        employees = Employe.objects.filter(poste__departement_id=selected_dept)

    if request.method == 'POST':
        date = request.POST.get('date')
        emp_ids = request.POST.getlist('employees')
        h_arrivee = request.POST.get('heure_arrivee', '08:00')
        h_depart = request.POST.get('heure_depart', '17:00')
        
        for emp_id in emp_ids:
            # Vérifier que l'employé appartient au département si manager
            emp = get_object_or_404(Employe, id=emp_id)
            if not request.user.is_superuser:
                profil = request.user.profil
                if not profil.is_rh and emp.poste.departement != profil.poste.departement:
                    continue

            Presence.objects.create(
                employe_id=emp_id,
                date=date,
                heure_arrivee=h_arrivee,
                heure_depart=h_depart
            )
        messages.success(request, f"Présences enregistrées.")
        return redirect('employees:presence_list')

    return render(request, 'employees/presence_form.html', {
        'departements': departements,
        'employees': employees,
        'selected_dept': selected_dept,
    })

@login_required
def presence_check(request):
    if request.user.is_superuser:
        messages.error(request, "Le superadmin ne peut pas pointer (pas de profil employé).")
        return redirect('employees:presence_list')
        
    profil = request.user.profil
    today = timezone.now().date()
    now = timezone.now().time()
    
    presence = Presence.objects.filter(employe=profil, date=today).first()
    
    if not presence:
        # Arrivée
        Presence.objects.create(
            employe=profil,
            date=today,
            heure_arrivee=now
        )
        messages.success(request, f"Arrivée enregistrée à {now.strftime('%H:%M')}.")
    elif not presence.heure_depart:
        # Départ
        presence.heure_depart = now
        presence.save()
        messages.success(request, f"Départ enregistré à {now.strftime('%H:%M')}.")
    else:
        messages.warning(request, "Vous avez déjà enregistré votre arrivée et votre départ pour aujourd'hui.")
        
    return redirect('employees:presence_list')

# Gestion de la Paie
@login_required
@rh_required
def paie_list(request):
    fiches = FichePaie.objects.all().select_related('employe').order_by('-annee', '-mois')
    return render(request, 'employees/paie_list.html', {'fiches': fiches})

@login_required
@rh_required
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
    user_registrations = []
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh:
            # Employé et DeptAdmin ne voient que les formations de leur département ou générales
            if profil.poste:
                formations = formations.filter(Q(departement=profil.poste.departement) | Q(departement__isnull=True))
            else:
                formations = formations.filter(departement__isnull=True)
                
        user_registrations = InscriptionFormation.objects.filter(
            employe=profil
        ).values_list('formation_id', flat=True)
    
    return render(request, 'employees/formation_list.html', {
        'formations': formations,
        'user_registrations': user_registrations
    })

@login_required
@manager_required
def formation_create(request):
    if request.method == 'POST':
        form = FormationForm(request.POST)
        if form.is_valid():
            formation = form.save(commit=False)
            # Isolation par département pour les managers
            if not request.user.is_superuser:
                profil = request.user.profil
                if not profil.is_rh and not profil.is_superadmin:
                    if profil.poste:
                        formation.departement = profil.poste.departement
            formation.save()
            messages.success(request, "Formation créée avec succès.")
            return redirect('employees:formation_list')
    else:
        form = FormationForm()
        if not request.user.is_superuser:
            profil = request.user.profil
            if not profil.is_rh and not profil.is_superadmin and profil.poste:
                form.initial['departement'] = profil.poste.departement

    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Créer une formation"})

@login_required
def formation_detail(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    # Restriction par département
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if formation.departement and (not profil.poste or formation.departement != profil.poste.departement):
                raise PermissionDenied

    inscriptions = InscriptionFormation.objects.filter(formation=formation).select_related('employe')
    
    is_registered = False
    user_inscription = None
    if not request.user.is_superuser and hasattr(request.user, 'profil'):
        user_inscription = inscriptions.filter(employe=request.user.profil).first()
        is_registered = user_inscription is not None
        
    return render(request, 'employees/formation_detail.html', {
        'formation': formation, 
        'inscriptions': inscriptions,
        'is_registered': is_registered,
        'user_inscription': user_inscription
    })

@login_required
@manager_required
def formation_update(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    # Restriction pour les managers
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if formation.departement and (not profil.poste or formation.departement != profil.poste.departement):
                raise PermissionDenied

    if request.method == 'POST':
        form = FormationForm(request.POST, instance=formation)
        if form.is_valid():
            form.save()
            messages.success(request, "Formation mise à jour.")
            return redirect('employees:formation_list')
    else:
        form = FormationForm(instance=formation)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier la formation"})

@login_required
@manager_required
def formation_delete(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    
    # Restriction pour les managers
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if formation.departement and (not profil.poste or formation.departement != profil.poste.departement):
                raise PermissionDenied
    if request.method == 'POST':
        formation.delete()
        messages.success(request, "Formation supprimée.")
        return redirect('employees:formation_list')
    return render(request, 'employees/confirm_delete.html', {'object': formation})

@login_required
def formation_register(request, pk):
    formation = get_object_or_404(Formation, pk=pk)
    if not hasattr(request.user, 'profil'):
        messages.error(request, "Vous devez avoir un profil employé pour vous inscrire.")
        return redirect('employees:formation_list')
    
    employe = request.user.profil
    
    # Vérifier si déjà inscrit
    if InscriptionFormation.objects.filter(employe=employe, formation=formation).exists():
        messages.warning(request, "Vous êtes déjà inscrit à cette formation.")
    else:
        InscriptionFormation.objects.create(employe=employe, formation=formation)
        messages.success(request, f"Votre inscription à la formation '{formation.titre}' a été enregistrée.")
    
    # Rediriger vers la page d'origine ou vers la liste des formations
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('employees:formation_list')

@login_required
@manager_required
def formation_inscription_update(request, pk, inscription_pk):
    inscription = get_object_or_404(
        InscriptionFormation.objects.select_related('formation'),
        pk=inscription_pk,
        formation_id=pk
    )

    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if inscription.formation.departement and (not profil.poste or inscription.formation.departement != profil.poste.departement):
                raise PermissionDenied

    if request.method != 'POST':
        return redirect('employees:formation_detail', pk=pk)

    form = InscriptionFormationUpdateForm(request.POST, request.FILES, instance=inscription)
    if form.is_valid():
        form.save()
        messages.success(request, "Inscription mise à jour.")
    else:
        messages.error(request, "Impossible de mettre à jour l'inscription.")
    return redirect('employees:formation_detail', pk=pk)

# Recrutements
@login_required
def recrutement_list(request):
    offres = OffreEmploi.objects.all().annotate(num_candidatures=Count('candidatures'))
    
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_superadmin and not profil.is_rh:
            # Employé et DeptAdmin ne voient que leur département
            if profil.poste:
                offres = offres.filter(departement=profil.poste.departement)
            else:
                offres = offres.none()
            
    return render(request, 'employees/recrutement_list.html', {'offres': offres})

@login_required
@manager_required
def recrutement_create(request):
    if request.method == 'POST':
        form = OffreEmploiForm(request.POST)
        if form.is_valid():
            offre = form.save(commit=False)
            if not request.user.is_superuser:
                profil = request.user.profil
                if not profil.is_rh and not profil.is_superadmin:
                    if profil.poste:
                        offre.departement = profil.poste.departement
            offre.save()
            messages.success(request, "Offre d'emploi publiée.")
            return redirect('employees:recrutement_list')
    else:
        form = OffreEmploiForm()
        if not request.user.is_superuser:
            profil = request.user.profil
            if not profil.is_rh and not profil.is_superadmin and profil.poste:
                form.initial['departement'] = profil.poste.departement
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Publier une offre"})

@login_required
def recrutement_detail(request, pk):
    offre = get_object_or_404(OffreEmploi.objects.annotate(num_candidatures=Count('candidatures')), pk=pk)
    
    # Permission de voir
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_superadmin and not profil.is_rh:
            if not profil.poste or offre.departement != profil.poste.departement:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
                
    candidatures = offre.candidatures.all()
    # Seuls RH/SuperAdmin voient les candidatures détaillées
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_superadmin and not profil.is_rh:
            candidatures = []
            
    return render(request, 'employees/recrutement_detail.html', {'offre': offre, 'candidatures': candidatures})

@login_required
@manager_required
def recrutement_update(request, pk):
    offre = get_object_or_404(OffreEmploi, pk=pk)
    
    # Restriction pour les managers
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if offre.departement and (not profil.poste or offre.departement != profil.poste.departement):
                raise PermissionDenied

    if request.method == 'POST':
        form = OffreEmploiForm(request.POST, instance=offre)
        if form.is_valid():
            form.save()
            messages.success(request, "Offre d'emploi mise à jour.")
            return redirect('employees:recrutement_list')
    else:
        form = OffreEmploiForm(instance=offre)
    return render(request, 'employees/employee_form.html', {'form': form, 'title': "Modifier l'offre"})

@login_required
@manager_required
def recrutement_delete(request, pk):
    offre = get_object_or_404(OffreEmploi, pk=pk)
    
    # Restriction pour les managers
    if not request.user.is_superuser:
        profil = request.user.profil
        if not profil.is_rh and not profil.is_superadmin:
            if offre.departement and (not profil.poste or offre.departement != profil.poste.departement):
                raise PermissionDenied

    if request.method == 'POST':
        offre.delete()
        messages.success(request, "Offre d'emploi supprimée.")
        return redirect('employees:recrutement_list')
    return render(request, 'employees/confirm_delete.html', {'object': offre})

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
@manager_required
def politique_list(request):
    types_contrat = TypeContrat.objects.all()
    return render(request, 'employees/politique_list.html', {'types_contrat': types_contrat})

@login_required
@manager_required
def politique_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        if nom:
            TypeContrat.objects.create(nom=nom, description=description)
            return redirect('employees:politique_list')
    return render(request, 'employees/politique_form.html', {'title': "Ajouter un type de contrat"})
