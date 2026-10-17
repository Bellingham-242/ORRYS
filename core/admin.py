from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, Publication, Rapport, ServiceRequest, 
    Transaction, QuestionReponse, SystemConfig
)


# --- CONFIGURATION UTILISATEUR (CUSTOM USER) ---
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'role_badge', 'is_approved_status', 'email', 'phone', 'is_staff')
    list_filter = ('role', 'is_approved', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    ordering = ('role', '-date_joined')

    fieldsets = UserAdmin.fieldsets + (
        ('Informations Spécifiques ORRYS', {
            'fields': ('role', 'is_approved', 'phone', 'photo'),
            'description': 'Paramètres de compte et quotas système.'
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Spécifiques ORRYS', {
            'fields': ('role', 'is_approved', 'phone', 'photo'),
        }),
    )

    def role_badge(self, obj):
        colors = {
            'ADMIN': '#B01E44',        # Rouge ORRYS
            'GESTIONNAIRE': '#00B7F1',  # Bleu ORRYS
            'EMPLOYE': '#28a745',       # Vert
            'CLIENT': '#6c757d',        # Gris
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 10px;">{}</span>',
            colors.get(obj.role, '#000'),
            obj.get_role_display()
        )
    role_badge.short_description = "Rôle"

    def is_approved_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: #28a745;">✔ Approuvé</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">✘ En attente</span>')
    is_approved_status.short_description = "Validation"


# --- CONFIGURATION SYSTÈME (SINGLETON) ---
@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_email', 'company_phone', 'currency', 'maintenance_mode')
    
    def has_add_permission(self, request):
        # Empêche la création de multiples configurations
        if SystemConfig.objects.exists():
            return False
        return super().has_add_permission(request)


# --- GESTION DE LA CAISSE (TRANSACTIONS) ---
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date_creation', 'motif', 'type_badge', 'montant_display', 'auteur')
    list_filter = ('type', 'date_creation', 'auteur')
    search_fields = ('motif', 'description')
    readonly_fields = ('date_creation', 'auteur')
    list_per_page = 15

    def type_badge(self, obj):
        color = "#28a745" if obj.type == 'ENTREE' else "#dc3545"
        return format_html('<b style="color: {};">{}</b>', color, obj.get_type_display())
    type_badge.short_description = "Type"

    def montant_display(self, obj):
        prefix = "+" if obj.type == 'ENTREE' else "-"
        montant_formate = "{:,.0f}".format(obj.montant).replace(',', ' ')
        return format_html(
            '<b style="color: {};">{} {} FCFA</b>',
            "#28a745" if obj.type == 'ENTREE' else "#dc3545",
            prefix,
            montant_formate
        )
    montant_display.short_description = "Montant"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.auteur = request.user
        super().save_model(request, obj, form, change)


# --- SERVICES ET REQUÊTES CLIENTS ---
@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_client', 'nature', 'is_read', 'date_requested')
    list_filter = ('is_read', 'date_requested')
    search_fields = ('nature', 'explanation', 'client__username')

    @admin.display(description='Client')
    def get_client(self, obj):
        return obj.client.get_full_name() or obj.client.username


# --- PUBLICATIONS ET RAPPORTS ---
@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'date_creation')
    list_filter = ('status', 'date_creation')
    list_editable = ('status',)
    search_fields = ('title', 'content')

    def save_model(self, request, obj, form, change):
        if not change and not hasattr(obj, 'author'):
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ('title', 'employee', 'date_submission')
    readonly_fields = ('date_submission',)
    list_filter = ('employee', 'date_submission')


# --- FAQ (QUESTIONS / RÉPONSES) ---
@admin.register(QuestionReponse)
class QuestionReponseAdmin(admin.ModelAdmin):
    list_display = ('name', 'question_preview', 'is_published', 'date_ask')
    list_editable = ('is_published',)

    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = "Question"