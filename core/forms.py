from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, SystemConfig, ServiceRequest, Transaction, Publication, Rapport, QuestionReponse


# --- CLASSE DE BASE POUR INJECTION BOOTSTRAP 5 ---
class BootstrapModelForm(forms.ModelForm):
    """Classe parente réutilisable pour styliser automatiquement tous les formulaires."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control rounded-3', 'rows': 4})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})


# --- CONFIGURATION SYSTÈME ---
class SystemConfigForm(BootstrapModelForm):
    class Meta:
        model = SystemConfig
        fields = '__all__'


# --- REQUÊTE SERVICE CLIENT ---
class ServiceRequestForm(BootstrapModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['nature', 'explanation', 'image']
        labels = {
            'nature': 'Nature de la demande',
            'explanation': 'Explication détaillée',
            'image': 'Fichier / Pièce jointe (optionnel)'
        }


# --- CAISSE & TRANSACTIONS ---
class TransactionForm(BootstrapModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'montant', 'motif', 'description', 'image']
        widgets = {
            'montant': forms.NumberInput(attrs={'step': '100', 'min': '0'}),
        }


# --- PUBLICATIONS ---
class PublicationForm(BootstrapModelForm):
    class Meta:
        model = Publication
        fields = ['title', 'content', 'image', 'status']


# --- RAPPORTS D'ACTIVITÉ ---
class RapportForm(BootstrapModelForm):
    class Meta:
        model = Rapport
        fields = ['title', 'content', 'image']


# --- FAQ (QUESTIONS / RÉPONSES) ---
class QuestionReponseForm(BootstrapModelForm):
    class Meta:
        model = QuestionReponse
        fields = ['name', 'question']


# --- GESTION UTILISATEURS ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'photo', 'is_approved')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select rounded-3'})
            else:
                field.widget.attrs.update({'class': 'form-control rounded-3'})