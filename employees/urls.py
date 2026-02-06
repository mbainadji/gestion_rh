from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Employés
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/<int:employee_pk>/documents/add/', views.document_create, name='document_create'),
    
    # Départements
    path('departements/', views.departement_list, name='departement_list'),
    path('departements/add/', views.departement_create, name='departement_create'),
    path('departements/<int:pk>/', views.departement_detail, name='departement_detail'),
    path('departements/<int:pk>/edit/', views.departement_update, name='departement_update'),
    path('departements/<int:pk>/delete/', views.departement_delete, name='departement_delete'),
    
    # Postes
    path('postes/', views.poste_list, name='poste_list'),
    path('postes/add/', views.poste_create, name='poste_create'),
    path('postes/<int:pk>/', views.poste_detail, name='poste_detail'),
    path('postes/<int:pk>/edit/', views.poste_update, name='poste_update'),
    path('postes/<int:pk>/delete/', views.poste_delete, name='poste_delete'),
    
    # Congés
    path('conges/', views.conge_list, name='conge_list'),
    path('conges/request/', views.conge_request, name='conge_request'),
    path('conges/<int:pk>/approve/', views.conge_approve, name='conge_approve'),
    path('conges/<int:pk>/reject/', views.conge_reject, name='conge_reject'),
    
    # Présences
    path('presences/', views.presence_list, name='presence_list'),
    path('presences/add/', views.presence_create, name='presence_create'),
    
    # Paie
    path('paie/', views.paie_list, name='paie_list'),
    path('paie/add/', views.paie_create, name='paie_create'),
    
    # Formations
    path('formations/', views.formation_list, name='formation_list'),
    path('formations/add/', views.formation_create, name='formation_create'),
    path('formations/<int:pk>/', views.formation_detail, name='formation_detail'),
    path('formations/<int:pk>/edit/', views.formation_update, name='formation_update'),
    path('formations/<int:pk>/delete/', views.formation_delete, name='formation_delete'),
    
    # Recrutement
    path('recrutements/', views.recrutement_list, name='recrutement_list'),
    path('recrutements/add/', views.recrutement_create, name='recrutement_create'),
    path('recrutements/<int:pk>/', views.recrutement_detail, name='recrutement_detail'),
    path('recrutements/<int:pk>/edit/', views.recrutement_update, name='recrutement_update'),
    path('recrutements/<int:pk>/delete/', views.recrutement_delete, name='recrutement_delete'),
    
    # Export
    path('employees/export/csv/', views.export_employees_csv, name='export_employees_csv'),
    
    # Politiques
    path('politiques/', views.politique_list, name='politique_list'),
    path('politiques/add/', views.politique_create, name='politique_create'),
]
