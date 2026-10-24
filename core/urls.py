from django.urls import path
from . import views

urlpatterns = [
    # --- Pages Publiques ---
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('team/', views.team, name='team'),
    path('testimonials/', views.testimonials, name='testimonials'),

    # --- Authentification ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Dashboards ---
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/gestionnaire/', views.gestionnaire_dashboard, name='gestionnaire_dashboard'),
    path('dashboard/employe/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/client/', views.client_dashboard_view, name='client_dashboard'),
    path('services/', views.client_dashboard_view, name='services'), # Pointer vers la vue POST
    path('dashboard/admin/user/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('dashboard/admin/user/<int:user_id>/reject/', views.reject_user, name='reject_user'),
    path('service/<int:pk>/traiter/', views.marquer_traite_service, name='marquer_traite_service'),

    # --- Gestion des Rapports ---
    path('dashboard/employe/rapport/nouveau/', views.soumettre_rapport, name='soumettre_rapport'),
    path('admin-espace/rapports/', views.admin_reports_list, name='admin_reports_list'),
    path('admin-espace/rapports/delete/<int:report_id>/', views.delete_report, name='delete_report'),

    # --- Gestion de Caisse ---
    path('caisse/',views.gestion_caisse, name='gestion_caisse'),
    path('caisse/supprimer/<int:transaction_id>/', views.confirmer_suppression_transaction, name='confirmer_suppression_transaction'),
    path('caisse/modifier/<int:transaction_id>/', views.modifier_transaction, name='modifier_transaction'),
    path('caisse/preuve/<int:transaction_id>/', views.voir_preuve_caisse, name='voir_preuve_caisse'),

    # --- Gestion des Utilisateurs & Clients ---
    path('utilisateurs/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    # Page principale de gestion des utilisateurs
    path('users/', views.user_management_view, name='user_management'),
    
    # # Routes d'action pour les modales (Modification & Suppression)
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('dashboard/clients/attente/', views.liste_clients_en_attente, name='clients_attente'),
    path('dashboard/clients/approuver/<int:user_id>/', views.approuver_client, name='approuver_client'),

    # --- Publications & Archives ---
    path('publications/', views.publications_view, name='publications_list'),
    path('dashboard/archives/publication/edit/<int:pk>/', views.edit_publication, name='edit_publication'),
    path('dashboard/archives/publication/delete/<int:pk>/', views.delete_publication, name='delete_publication'),
    path('dashboard/archives/', views.archives_view, name='archives'),
    path('settings/', views.settings_view, name='settings'),
    path('service/<int:request_id>/repondre/', views.repondre_demande_service, name='repondre_demande_service'),
]

# Optionnel : si tu souhaites utiliser ta vue error_404 personnalisée dans le urls.py principal du projet :
# handler404 = 'nom_de_ton_app.views.error_404'