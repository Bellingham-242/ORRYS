from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('GESTIONNAIRE', 'Gestionnaire'),
        ('EMPLOYE', 'Employé'),
        ('CLIENT', 'Client'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENT')
    is_approved = models.BooleanField(default=False)  # Pour la validation Admin/Gestionnaire
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def clean(self):
        # Vérification des quotas avant enregistrement
        if self.role == 'ADMIN' and User.objects.filter(role='ADMIN').count() >= 3 and not self.pk:
            raise ValidationError("Quota atteint : Maximum 3 Administrateurs.")
        if self.role == 'GESTIONNAIRE' and User.objects.filter(role='GESTIONNAIRE').count() >= 4 and not self.pk:
            raise ValidationError("Quota atteint : Maximum 4 Gestionnaires.")
        if self.role == 'EMPLOYE' and User.objects.filter(role='EMPLOYE').count() >= 30 and not self.pk:
            raise ValidationError("Quota atteint : Maximum 30 Employés.")
        if self.role == 'CLIENT' and User.objects.filter(role='CLIENT').count() >= 100 and not self.pk:
            raise ValidationError("Quota atteint : Maximum 100 Clients.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        
class Publication(models.Model):
    STATUS_CHOICES = [('PENDING', 'En attente'), ('PUBLIC', 'Public'), ('LOCAL', 'Local')]
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='publications/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    date_creation = models.DateTimeField(auto_now_add=True)

class Rapport(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'EMPLOYE'})
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='reports/', blank=True, null=True)
    date_submission = models.DateTimeField(auto_now_add=True)

    
    
class Transaction(models.Model):
    TYPE_CHOICES = [('ENTREE', 'Entrée'), ('SORTIE', 'Sortie')]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    motif = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='caisse/', blank=True, null=True)
    auteur = models.ForeignKey(User, on_delete=models.PROTECT)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        
        
class QuestionReponse(models.Model):
    name = models.CharField(max_length=100) # Nom ou surnom
    question = models.TextField()
    reponse = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    date_ask = models.DateTimeField(auto_now_add=True)


class SystemConfig(models.Model):
    # --- Identité Entreprise ---
    company_name = models.CharField("Nom de la structure", max_length=150, default="ORRYS NUMERIQUE")
    company_slogan = models.CharField("Slogan / Sous-titre", max_length=255, default="Management & Digital Solutions", blank=True)
    company_email = models.EmailField("Email officiel", default="contact@orrys.com", blank=True)
    company_phone = models.CharField("Téléphone support", max_length=50, default="+242 06 000 0000", blank=True)
    company_address = models.CharField("Adresse physique", max_length=255, default="Pointe-Noire, République du Congo", blank=True)
    company_logo = models.ImageField("Logo de l'entreprise", upload_to="company/", blank=True, null=True)
    company_nif = models.CharField("Matricule Fiscal / NIF", max_length=50, blank=True)

    # --- Caisse & Facturation ---
    CURRENCY_CHOICES = [
        ('XAF', 'FCFA (XAF)'),
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar ($)'),
    ]
    currency = models.CharField("Devise", max_length=10, choices=CURRENCY_CHOICES, default='XAF')
    default_tva = models.DecimalField("Taux de TVA (%)", max_digits=5, decimal_places=2, default=18.0)
    caisse_min_threshold = models.DecimalField("Seuil alerte caisse basse", max_digits=12, decimal_places=2, default=50000)
    momo_number = models.CharField("Numéro MTN Mobile Money", max_length=30, blank=True)
    airtel_number = models.CharField("Numéro Airtel Money", max_length=30, blank=True)
    receipt_footer = models.TextField("Pied de page des reçus", default="Merci pour votre confiance !", blank=True)

    # --- Sécurité ---
    enforce_2fa = models.BooleanField("Exiger 2FA pour les admins", default=False)
    auto_logout = models.BooleanField("Déconnexion automatique après inactivité", default=True)
    session_timeout = models.IntegerField("Inactivité (minutes)", default=30)
    min_password_len = models.IntegerField("Longueur min du mot de passe", default=8)

    # --- Notifications ---
    smtp_host = models.CharField("Serveur SMTP", max_length=150, blank=True, default="smtp.gmail.com")
    smtp_port = models.IntegerField("Port SMTP", default=587)
    sms_api_key = models.CharField("Clé API SMS/WhatsApp", max_length=255, blank=True)
    notify_new_client = models.BooleanField("Notifier lors d'une inscription client", default=True)

    # --- Intégrations ---
    cloud_backup_enabled = models.BooleanField("Sauvegarde Cloud automatique", default=True)
    momo_webhook_enabled = models.BooleanField("Webhooks Mobile Money API", default=False)

    # --- Maintenance ---
    maintenance_mode = models.BooleanField("Activer Mode Maintenance", default=False)

    class Meta:
        verbose_name = "Configuration Système"
        verbose_name_plural = "Configuration Système"

    def __str__(self):
        return f"Configuration - {self.company_name}"

    @classmethod
    def get_solo(cls):
        """Récupère la configuration unique ou en crée une par défaut."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class ServiceRequest(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'CLIENT'},related_name='service_requests')
    nature = models.CharField(max_length=200)
    explanation = models.TextField()
    image = models.ImageField(upload_to='requests/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    date_requested = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demande de service"
        verbose_name_plural = "Demandes de service"
        ordering = ['-date_requested']

    def __str__(self):
        return f"{self.nature} - {self.client.username}"


class ServiceRequest(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'CLIENT'}, related_name='service_requests')
    nature = models.CharField(max_length=200)
    explanation = models.TextField()
    image = models.ImageField(upload_to='requests/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    
    # NOUVEAUX CHAMPS DE RÉPONSE
    response = models.TextField("Réponse de l'administration", blank=True, null=True)
    date_responded = models.DateTimeField("Date de réponse", blank=True, null=True)
    
    date_requested = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demande de service"
        verbose_name_plural = "Demandes de service"
        ordering = ['-date_requested']

    def __str__(self):
        return f"{self.nature} - {self.client.username}"