import random
import string
import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from .forms import SystemConfigForm
# Ajoutez ServiceRequestForm dans vos imports de formulaires :
from .forms import ServiceRequestForm,SystemConfigForm,TransactionForm,PublicationForm,RapportForm,QuestionReponseForm,CustomUserCreationForm,CustomUserChangeForm

from .models import User, Transaction, Rapport, ServiceRequest, Publication, QuestionReponse,SystemConfig


# ==========================================
# 1. UTILITAIRES
# ==========================================

def generate_security_code(length=5):
    """Génère un code alphanumérique pour sécuriser les opérations sensibles."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def is_staff_member(user):
    """Vérifie si l'utilisateur est Admin ou Gestionnaire."""
    return user.is_authenticated and user.role in ['ADMIN', 'GESTIONNAIRE']


# ==========================================
# 2. PAGES PUBLIQUES
# ==========================================

def index(request):
    """Page d'accueil."""
    return render(request, 'index.html')

def about(request):
    """Page À propos."""
    return render(request, 'about.html')

def contact(request):
    """Page Contact."""
    return render(request, 'contact.html')

def services(request):
    """Page Liste des services."""
    return render(request, 'courses.html')

def team(request):
    """Page Présentation de l'équipe."""
    return render(request, 'team.html')

def testimonials(request):
    """Page Témoignages."""
    return render(request, 'testimonial.html')

def error_404(request, exception=None):
    """Page d'erreur 404 personnalisée."""
    return render(request, '404.html', status=404)


# ==========================================
# 3. AUTHENTIFICATION & COMPTES
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        if request.user.role in ['ADMIN', 'GESTIONNAIRE']:
            return redirect('admin_dashboard')
        elif request.user.role == 'EMPLOYE':
            return redirect('employee_dashboard')
        return redirect('client_dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        
        if user is not None:
            if user.role == 'CLIENT' and not user.is_approved:
                messages.error(request, "Accès refusé. Votre compte est en attente de validation.")
            else:
                login(request, user)
                if user.role in ['ADMIN', 'GESTIONNAIRE']:
                    return redirect('admin_dashboard')
                elif user.role == 'EMPLOYE':
                    return redirect('employee_dashboard')
                return redirect('client_dashboard')
        else:
            messages.error(request, "Identifiants incorrects.")
            
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Déconnexion réussie.")
    return redirect('login')

@login_required
def ajouter_utilisateur(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Accès réservé à l'administrateur.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role')
        phone = request.POST.get('phone', '')
        photo = request.FILES.get('photo')

        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'dashboards/create_user.html')

        try:
            user = User(
                username=username,
                email=email,
                role=role,
                phone=phone,
                photo=photo,
                is_approved=False
            )
            user.set_password(password)
            # save() déclenche full_clean() et vérifie les quotas
            user.save()

            messages.success(request, f"Compte {role} créé pour {username}. En attente d'approbation.")
            return redirect('admin_dashboard')

        except ValidationError as e:
            messages.error(request, e.messages[0])
        except Exception as e:
            messages.error(request, f"Erreur lors de la création : {e}")

    return render(request, 'dashboards/create_user.html')


# ==========================================
# 4. DASHBOARDS
# ==========================================

@login_required
def admin_dashboard(request):
    # 1. Contrôle d'accès EN PREMIER (évite d'exécuter des requêtes DB inutiles)
    if getattr(request.user, 'role', None) not in ['ADMIN', 'GESTIONNAIRE']:
        return redirect('login')

    # 2. Calcul du solde financier
    entrees = Transaction.objects.filter(type='ENTREE').aggregate(Sum('montant'))['montant__sum'] or 0
    sorties = Transaction.objects.filter(type='SORTIE').aggregate(Sum('montant'))['montant__sum'] or 0
    solde_total = entrees - sorties

    # 3. Récupération des données (avec select_related pour optimiser les performances)
    service_requests = ServiceRequest.objects.select_related('client').all().order_by('-date_requested')
    transactions = Transaction.objects.all().order_by('-date_creation')[:15]
    clients_pending = User.objects.filter(is_approved=False, is_staff=False)

    # 4. Contexte envoyé au template
    context = {
        'service_requests': service_requests,
        'transactions': transactions,
        'solde_total': solde_total,
        'pending_clients': clients_pending.count(),
        'clients_pending_list': clients_pending,
        'total_employees': User.objects.filter(is_staff=True).count(),
        'total_clients': User.objects.filter(is_staff=False).count(),
    }
    
    return render(request, 'dashboards/admin.html', context)

@login_required
def gestionnaire_dashboard(request):
    if request.user.role not in ['GESTIONNAIRE', 'ADMIN']:
        return redirect('login')

    context = {
        'recent_transactions': Transaction.objects.all().order_by('-date_creation')[:15],
        'pending_clients': User.objects.filter(role='CLIENT', is_approved=False).count(),
    }
    return render(request, 'dashboards/gestionnaire.html', context)

@login_required
def employee_dashboard(request):
    if request.user.role != 'EMPLOYE' and not request.user.is_staff:
        return redirect('login')

    mes_rapports = Rapport.objects.filter(employee=request.user).order_by('-date_submission')
    mes_activites_caisse = Transaction.objects.filter(auteur=request.user)[:10]
    publications_locales = Publication.objects.filter(status='LOCAL').order_by('-date_creation')

    context = {
        'mes_rapports': mes_rapports,
        'mes_activites_caisse': mes_activites_caisse,
        'publications_locales': publications_locales,
        'total_rapports': mes_rapports.count(),
    }
    return render(request, 'dashboards/employee.html', context)



# --- DASHBOARD CLIENT CORRIGÉ ---
@login_required
def client_dashboard_view(request):
    if request.method == 'POST':
        nature = request.POST.get('nature')
        explanation = request.POST.get('explanation')
        image = request.FILES.get('image')

        if nature and explanation:
            ServiceRequest.objects.create(
                client=request.user,
                nature=nature,
                explanation=explanation,
                image=image
            )
            messages.success(request, "Votre demande a été transmise avec succès aux équipes d'ORRYS !")
            return redirect('client_dashboard')
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")

    service_requests = ServiceRequest.objects.filter(client=request.user).order_by('-date_requested')
    return render(request, 'dashboards/client.html', {'service_requests': service_requests})


# ==========================================
# 5. GESTION DE LA CAISSE
# ==========================================

@login_required
def gestion_caisse(request):
    if request.user.role not in ['ADMIN', 'GESTIONNAIRE']:
        messages.error(request, "Accès restreint au personnel autorisé.")
        return redirect('index')

    if request.method == 'POST':
        code_saisi = request.POST.get('security_code')
        code_attendu = request.session.get('current_security_code')

        if code_saisi != code_attendu:
            messages.error(request, "Protocole de sécurité échoué : Code incorrect.")
        else:
            type_t = request.POST.get('type')
            montant = request.POST.get('montant')
            motif = request.POST.get('motif')
            description_saisie = request.POST.get('description', '').strip()
            
            emp_id = request.POST.get('concerne_employe')
            info_employe = ""
            if emp_id:
                try:
                    employe = User.objects.get(id=emp_id)
                    info_employe = f" | Concerné : {employe.username}"
                except User.DoesNotExist:
                    pass

            Transaction.objects.create(
                type=type_t,
                montant=montant,
                motif=motif,
                description=f"{description_saisie}{info_employe}".strip(),
                auteur=request.user,
                image=request.FILES.get('image')
            )
            messages.success(request, f"Transaction de {montant} XAF enregistrée.")
            return redirect('gestion_caisse')

    # Pagination des transactions
    transactions_list = Transaction.objects.all().order_by('-date_creation')
    paginator = Paginator(transactions_list, 15)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    # Nouveau code de sécurité pour la session
    sec_code = generate_security_code(5)
    request.session['current_security_code'] = sec_code

    return render(request, 'dashboards/caisse.html', {
        'transactions': transactions,
        'security_code': sec_code,
        'employes': User.objects.filter(role='EMPLOYE')
    })

@login_required
def modifier_transaction(request, transaction_id):
    if request.user.role not in ['ADMIN', 'GESTIONNAIRE']:
        messages.error(request, "Accès refusé. Seuls l'Administration et les Gestionnaires peuvent modifier les flux.")
        return redirect('gestion_caisse')

    transaction = get_object_or_404(Transaction, id=transaction_id)
    employes = User.objects.filter(role='EMPLOYE')

    if request.method == 'POST':
        if not request.POST.get('confirmation_modification'):
            messages.error(request, "Vous devez confirmer la modification sous votre responsabilité.")
            return redirect('modifier_transaction', transaction_id=transaction.id)

        transaction.type = request.POST.get('type')
        transaction.montant = request.POST.get('montant')
        transaction.motif = request.POST.get('motif')
        description_saisie = request.POST.get('description', '').strip()
        
        concerne_id = request.POST.get('concerne_employe')
        info_employe = ""
        if concerne_id:
            try:
                employe = User.objects.get(id=concerne_id)
                info_employe = f" | Concerné : {employe.username}"
            except User.DoesNotExist:
                pass

        transaction.description = f"{description_saisie}{info_employe}".strip()

        if 'image' in request.FILES:
            transaction.image = request.FILES['image']

        transaction.save()
        messages.success(request, f"La transaction #{transaction.id} a été mise à jour avec succès.")
        return redirect('gestion_caisse')

    return render(request, 'dashboards/modifier_caisse.html', {
        'transaction': transaction,
        'employes': employes,
    })

@login_required
def confirmer_suppression_transaction(request, transaction_id):
    if request.user.role != 'ADMIN':
        messages.error(request, "Accès refusé. Seul un administrateur peut supprimer une transaction.")
        return redirect('gestion_caisse')

    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.method == 'POST':
        code_entre = request.POST.get('code_confirmation')
        code_attendu = request.session.get('delete_token')

        if code_entre and code_entre == code_attendu:
            transaction.delete()
            request.session.pop('delete_token', None)
            messages.success(request, f"La transaction de {transaction.montant} FCFA a été supprimée avec succès.")
            return redirect('gestion_caisse')
        else:
            messages.error(request, "Code de sécurité incorrect. La suppression a été annulée.")
            return redirect('gestion_caisse')

    code = generate_security_code(6)
    request.session['delete_token'] = code

    return render(request, 'dashboards/confirm_delete_caisse.html', {
        'transaction': transaction,
        'security_code': code
    })

@login_required
def voir_preuve_caisse(request, transaction_id):
    if request.user.role not in ['ADMIN', 'GESTIONNAIRE']:
        messages.error(request, "Accès non autorisé.")
        return redirect('login')

    transaction = get_object_or_404(Transaction, id=transaction_id)

    if not transaction.image:
        messages.warning(request, "Aucune preuve visuelle n'a été jointe à cette transaction.")
        return redirect('gestion_caisse')

    return render(request, 'dashboards/voir_preuve.html', {'transaction': transaction})


# ==========================================
# 6. GESTION DES RAPPORTS
# ==========================================

@login_required
def soumettre_rapport(request):
    if request.method == 'POST':
        if request.user.role != 'EMPLOYE':
            messages.error(request, "Seul un employé actif peut soumettre un rapport.")
            return redirect('login')
            
        title = request.POST.get('title')
        content = request.POST.get('content')
        image = request.FILES.get('image')
        
        try:
            Rapport.objects.create(
                employee=request.user,
                title=title,
                content=content,
                image=image
            )
            messages.success(request, "Votre rapport a été soumis avec succès à la direction !")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi du rapport : {e}")
            
    return redirect('employee_dashboard')

@login_required
def admin_reports_list(request):
    if request.user.role not in ['ADMIN', 'GESTIONNAIRE']:
        messages.error(request, "Accès restreint.")
        return redirect('login')

    rapports = Rapport.objects.all().order_by('-date_submission')
    total_count = rapports.count()
    today_count = rapports.filter(date_submission__date=datetime.date.today()).count()

    context = {
        'rapports': rapports,
        'total_count': total_count,
        'today_count': today_count,
    }
    return render(request, 'dashboards/admin_reports.html', context)

@login_required
def delete_report(request, report_id):
    if request.user.role != 'ADMIN':
        messages.error(request, "Seul un administrateur peut supprimer un rapport.")
        return redirect('admin_reports_list')

    rapport = get_object_or_404(Rapport, id=report_id)
    rapport.delete()
    messages.success(request, "Le rapport a été définitivement supprimé.")
    return redirect('admin_reports_list')


# ==========================================
# 7. VALIDATION CLIENTS & ARCHIVES / PUBS
# ==========================================

@login_required
@user_passes_test(is_staff_member)
def liste_clients_en_attente(request):
    clients = User.objects.filter(role='CLIENT', is_approved=False)
    return render(request, 'dashboards/clients_attente.html', {'clients': clients})

@login_required
@user_passes_test(is_staff_member)
def approuver_client(request, user_id):
    client = get_object_or_404(User, id=user_id)
    client.is_approved = True
    client.is_active = True
    client.save()
    messages.success(request, f"Le client {client.username} a été approuvé avec succès.")
    return redirect('liste_clients_en_attente')

def publications_view(request):
    if request.user.is_authenticated and request.user.role != 'CLIENT':
        pubs = Publication.objects.filter(status__in=['PUBLIC', 'LOCAL']).order_by('-date_creation')
    else:
        pubs = Publication.objects.filter(status='PUBLIC').order_by('-date_creation')
    
    return render(request, 'publications/liste.html', {'pubs': pubs})

@login_required
def archives_view(request):
    search_query = request.GET.get('search', '')
    active_tab = request.GET.get('tab', 'rapports')

    rapports_list = Rapport.objects.all().order_by('-date_submission')
    if search_query:
        rapports_list = rapports_list.filter(
            Q(title__icontains=search_query) | 
            Q(employee__username__icontains=search_query)
        )
    
    paginator_r = Paginator(rapports_list, 10)
    page_r = request.GET.get('page_r')
    rapports = paginator_r.get_page(page_r)

    pubs_list = Publication.objects.all().order_by('-date_creation')
    if search_query:
        pubs_list = pubs_list.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    paginator_p = Paginator(pubs_list, 10)
    page_p = request.GET.get('page_p')
    publications = paginator_p.get_page(page_p)

    context = {
        'rapports': rapports,
        'publications': publications,
        'search_query': search_query,
        'active_tab': active_tab,
        'total_rapports': rapports_list.count(),
        'total_pubs': pubs_list.count(),
    }
    return render(request, 'dashboards/archives.html', context)


@login_required
@user_passes_test(is_staff_member)
def user_management_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # -------------------------------------------------------------
        # 1. CRÉATION D'UN UTILISATEUR
        # -------------------------------------------------------------
        if action == 'create':
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role', 'CLIENT')
            phone = request.POST.get('phone', '')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            photo = request.FILES.get('photo')

            if password != password_confirm:
                messages.error(request, "Les mots de passe ne correspondent pas.")
            elif User.objects.filter(username=username).exists():
                messages.error(request, f"Le nom d'utilisateur '{username}' est déjà pris.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, f"L'email '{email}' est déjà utilisé.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.role = role
                user.phone = phone
                if photo:
                    user.photo = photo
                user.save()
                messages.success(request, f"L'utilisateur @{username} a été créé avec succès !")

        # -------------------------------------------------------------
        # 2. MODIFICATION D'UN UTILISATEUR
        # -------------------------------------------------------------
        elif action == 'edit':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)

            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.role = request.POST.get('role', user.role)
            user.phone = request.POST.get('phone', user.phone)

            if request.FILES.get('photo'):
                user.photo = request.FILES.get('photo')

            user.save()
            messages.success(request, f"Le profil de @{user.username} a été mis à jour.")

        # -------------------------------------------------------------
        # 3. SUPPRESSION D'UN UTILISATEUR
        # -------------------------------------------------------------
        elif action == 'delete':
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)

            if user == request.user:
                messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            else:
                username = user.username
                user.delete()
                messages.success(request, f"L'utilisateur @{username} a été supprimé.")

        return redirect(request.path)

    # -------------------------------------------------------------
    # AFFICHAGE DE LA PAGE (GET)
    # -------------------------------------------------------------
    users = User.objects.all().order_by('-date_joined')
    staff_count = users.filter(role__in=['ADMIN', 'GESTIONNAIRE', 'EMPLOYE']).count()
    clients_count = users.filter(role='CLIENT').count()

    context = {
        'users': users,
        'staff_count': staff_count,
        'clients_count': clients_count,
    }
    return render(request, 'dashboards/user_management.html', context)

def edit_user(request, user_id):
    """Vue de modification appelée par l'URL users/edit/<id>/"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.role = request.POST.get('role', user.role)
        user.phone = request.POST.get('phone', user.phone)
        
        if request.FILES.get('photo'):
            user.photo = request.FILES.get('photo')
            
        try:
            user.save()
            messages.success(request, f"Le profil de @{user.username} a été mis à jour.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification : {e}")
            
    return redirect('user_management')


def delete_user(request, user_id):
    """Vue de suppression appelée par l'URL users/delete/<id>/"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        else:
            username = user.username
            user.delete()
            messages.success(request, f"L'utilisateur @{username} a été supprimé avec succès.")
            
    return redirect('user_management')

@login_required
def settings_view(request):
    # 1. Control d'accès (seuls ADMIN et GESTIONNAIRE peuvent modifier)
    if hasattr(request.user, 'role') and request.user.role not in ['ADMIN', 'GESTIONNAIRE']:
        messages.error(request, "Accès refusé : Autorisations insuffisantes.")
        return redirect('admin_dashboard')

    # 2. Récupération de l'instance unique de configuration
    config = SystemConfig.get_solo()

    if request.method == 'POST':
        form = SystemConfigForm(request.POST, request.FILES, instance=config)
        
        if form.is_valid():
            # Pré-enregistrement pour appliquer d'éventuelles modifications manuelles
            config_instance = form.save(commit=False)
            
            # Traitement sécurisé des cases à cocher (booléens)
            config_instance.enforce_2fa = 'enforce_2fa' in request.POST
            config_instance.auto_logout = 'auto_logout' in request.POST
            config_instance.notify_new_client = 'notify_new_client' in request.POST
            config_instance.cloud_backup_enabled = 'cloud_backup_enabled' in request.POST
            config_instance.momo_webhook_enabled = 'momo_webhook_enabled' in request.POST
            config_instance.maintenance_mode = 'maintenance_mode' in request.POST

            # Sauvegarde définitive en base de données
            config_instance.save()
            
            messages.success(request, "Les paramètres de configuration ont été mis à jour avec succès !")
            return redirect('settings')
        else:
            # Traitement de secours si le ModelForm est partiel ou si des champs POST sont hors du Form
            # (Garantit la sauvegarde même si les champs HTML sont gérés manuellement)
            fields_to_update = [
                'footer_about', 'footer_copyright', 'company_phone', 
                'company_email', 'company_address', 'social_facebook', 
                'social_whatsapp', 'social_linkedin', 'social_instagram'
            ]
            for field in fields_to_update:
                if field in request.POST:
                    setattr(config, field, request.POST.get(field, '').strip())
            
            # Sauvegarde directe de la configuration
            config.save()
            messages.success(request, "Les paramètres du pied de page ont été mis à jour !")
            return redirect('settings')
    else:
        form = SystemConfigForm(instance=config)

    # Récupération du nombre de clients en attente de validation
    pending_clients_count = User.objects.filter(role='CLIENT', is_approved=False).count() if hasattr(User, 'is_approved') else 0

    context = {
        'form': form,
        'config': config,
        'pending_clients': pending_clients_count,
    }
    return render(request, 'settings.html', context)

## Suite Du 04 Octobre 2026 

@login_required
def approve_user(request, user_id):
    # Vérification des droits d'accès
    if getattr(request.user, 'role', None) not in ['ADMIN', 'GESTIONNAIRE']:
        return redirect('login')

    if request.method == 'POST':
        client = get_object_or_404(User, id=user_id)
        client.is_approved = True
        client.save()
        messages.success(request, f"Le compte de {client.get_full_name() or client.username} a été validé.")

    return redirect('admin_dashboard')

@login_required
def reject_user(request, user_id):
    # Vérification des droits d'accès
    if getattr(request.user, 'role', None) not in ['ADMIN', 'GESTIONNAIRE']:
        return redirect('login')

    if request.method == 'POST':
        client = get_object_or_404(User, id=user_id)
        
        # Option A : Supprimer définitivement l'utilisateur de la base de données
        client.delete()
        
        # Option B (Alternative) : Désactiver le compte au lieu de le supprimer
        # client.is_approved = False
        # client.is_active = False
        # client.save()

        messages.warning(request, "La demande d'inscription a été rejetée.")

    return redirect('admin_dashboard')