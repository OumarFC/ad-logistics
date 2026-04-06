from django.db import models
from django.conf import settings

class EntrepriseCliente(models.Model):
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    ville = models.CharField(max_length=120, blank=True)
    pays = models.CharField(max_length=120, default="France")
    logo = models.ImageField(upload_to="entreprises/logos/", blank=True, null=True)

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Entreprise cliente"
        verbose_name_plural = "Entreprises clientes"

    def __str__(self):
        return self.nom


class Parametre(models.Model):
    TYPE_CHOICES = [
        ("text", "Texte"),
        ("number", "Nombre"),
        ("bool", "Oui / Non"),
        ("email", "Email"),
        ("phone", "Téléphone"),
        ("date", "Date"),
    ]

    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="entreprise",
        null=True,
        blank=True,
    )

    cle = models.CharField(max_length=100)
    libelle = models.CharField(max_length=150)
    valeur = models.TextField(blank=True, default="")
    type_valeur = models.CharField(max_length=20, choices=TYPE_CHOICES, default="text")
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=0)
    modifiable = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordre", "libelle"]
        unique_together = ("entreprise", "cle")
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        cible = self.entreprise.nom if self.entreprise else "Global"
        return f"{cible} - {self.libelle}: {self.valeur}"


class Agence(models.Model):
    TYPE_CHOICES = [
        ("PRINCIPALE", "Principale"),
        ("SECONDAIRE", "Secondaire"),
        ("PARTENAIRE", "Partenaire"),
    ]

    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="Agences",
        null=True,
        blank=True,
    )

    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    ville = models.CharField(max_length=120)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    responsable = models.CharField(max_length=150, blank=True)
    type_agence = models.CharField(max_length=20, choices=TYPE_CHOICES, default="SECONDAIRE")
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        unique_together = ("entreprise", "code")
        verbose_name = "Agence"
        verbose_name_plural = "Agences"

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"


class ProfilAgent(models.Model):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Admin"),
        ("ADMIN_CLIENT", "Admin client"),
        ("CHEF_AGENCE", "Chef d'agence"),
        ("AGENT", "Agent"),
        ("CAISSE", "Caisse"),
        ("LECTURE", "Lecture seule"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_agent"
    )
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="agents"
    )
    agence = models.ForeignKey(
        Agence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents"
    )

    telephone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="AGENT")
    actif = models.BooleanField(default=True)

    peut_gerer_agences = models.BooleanField(default=False)
    peut_gerer_agents = models.BooleanField(default=False)
    peut_gerer_parametres = models.BooleanField(default=False)
    peut_gerer_sms = models.BooleanField(default=False)
    peut_voir_factures = models.BooleanField(default=False)
    peut_voir_rapports = models.BooleanField(default=False)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Profil agent"
        verbose_name_plural = "Profils agents"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class VilleLivraison(models.Model):
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="villes_livraison"
    )
    nom = models.CharField(max_length=120)
    pays = models.CharField(max_length=120, default="Guinée")
    zone = models.CharField(max_length=120, blank=True)
    frais_livraison = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delai_estime_jours = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entreprise__nom", "nom"]
        unique_together = ("entreprise", "nom")
        verbose_name = "Ville de livraison"
        verbose_name_plural = "Villes de livraison"

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"
        
class ParametreSMS(models.Model):
    FOURNISSEUR_CHOICES = [
        ("BREVO", "Brevo"),
        ("TWILIO", "Twilio"),
        ("AUTRE", "Autre"),
    ]

    entreprise = models.OneToOneField(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="param_sms"
    )

    fournisseur = models.CharField(max_length=30, choices=FOURNISSEUR_CHOICES, default="BREVO")
    api_key = models.CharField(max_length=255, blank=True)
    sender_name = models.CharField(max_length=50, blank=True)
    sms_actif = models.BooleanField(default=False)

    modele_creation = models.TextField(blank=True)
    modele_arrivee = models.TextField(blank=True)
    modele_livraison = models.TextField(blank=True)
    modele_transfert = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entreprise__nom"]
        verbose_name = "Paramétrage SMS"
        verbose_name_plural = "Paramétrages SMS"

    def __str__(self):
        return f"SMS - {self.entreprise.nom}"

class EntrepriseCliente(models.Model):
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    ville = models.CharField(max_length=120, blank=True)
    pays = models.CharField(max_length=120, default="France")
    logo = models.ImageField(upload_to="entreprises/logos/", blank=True, null=True)

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Entreprise cliente"
        verbose_name_plural = "Entreprises clientes"

    def __str__(self):
        return self.nom


class Parametre(models.Model):
    TYPE_CHOICES = [
        ("text", "Texte"),
        ("number", "Nombre"),
        ("bool", "Oui / Non"),
        ("email", "Email"),
        ("phone", "Téléphone"),
        ("date", "Date"),
        ("textarea", "Texte long"),
        ("color", "Couleur"),
        ("image", "Image"),
        ("url", "URL"),
    ]

    CATEGORIE_CHOICES = [
        ("IDENTITE", "Identité société"),
        ("CONTACT", "Coordonnées"),
        ("AFFICHAGE", "Affichage"),
        ("FACTURATION", "Facturation"),
        ("REFERENCES", "Références"),
        ("TRACKING", "Tracking / QR Code"),
        ("AUTRE", "Autre"),
    ]

    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="parametres",
        null=True,
        blank=True,
    )

    categorie = models.CharField(
        max_length=30,
        choices=CATEGORIE_CHOICES,
        default="AUTRE"
    )

    cle = models.CharField(max_length=100)
    libelle = models.CharField(max_length=150)
    valeur = models.TextField(blank=True, default="")
    type_valeur = models.CharField(max_length=20, choices=TYPE_CHOICES, default="text")
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=0)
    modifiable = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    fichier = models.ImageField(upload_to="parametres/", blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["categorie", "ordre", "libelle"]
        unique_together = ("entreprise", "cle")
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        cible = self.entreprise.nom if self.entreprise else "Global"
        return f"{cible} - {self.libelle}: {self.valeur}"


class Agence(models.Model):
    TYPE_CHOICES = [
        ("PRINCIPALE", "Principale"),
        ("SECONDAIRE", "Secondaire"),
        ("PARTENAIRE", "Partenaire"),
    ]

    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="agences"
    )

    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    ville = models.CharField(max_length=120)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    responsable = models.CharField(max_length=150, blank=True)
    type_agence = models.CharField(max_length=20, choices=TYPE_CHOICES, default="SECONDAIRE")
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        unique_together = ("entreprise", "code")
        verbose_name = "Agence"
        verbose_name_plural = "Agences"

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"


class ProfilAgent(models.Model):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Admin"),
        ("ADMIN_CLIENT", "Admin client"),
        ("CHEF_AGENCE", "Chef d'agence"),
        ("AGENT", "Agent"),
        ("CAISSE", "Caisse"),
        ("LECTURE", "Lecture seule"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_agent"
    )
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="agents"
    )
    agence = models.ForeignKey(
        Agence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents"
    )

    telephone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="AGENT")
    actif = models.BooleanField(default=True)

    peut_gerer_agences = models.BooleanField(default=False)
    peut_gerer_agents = models.BooleanField(default=False)
    peut_gerer_parametres = models.BooleanField(default=False)
    peut_gerer_sms = models.BooleanField(default=False)
    peut_voir_factures = models.BooleanField(default=False)
    peut_voir_rapports = models.BooleanField(default=False)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        verbose_name = "Profil agent"
        verbose_name_plural = "Profils agents"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class VilleLivraison(models.Model):
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="villes_livraison"
    )
    nom = models.CharField(max_length=120)
    pays = models.CharField(max_length=120, default="Guinée")
    zone = models.CharField(max_length=120, blank=True)
    frais_livraison = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delai_estime_jours = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entreprise__nom", "nom"]
        unique_together = ("entreprise", "nom")
        verbose_name = "Ville de livraison"
        verbose_name_plural = "Villes de livraison"

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"


class ParametreSMS(models.Model):
    FOURNISSEUR_CHOICES = [
        ("BREVO", "Brevo"),
        ("TWILIO", "Twilio"),
        ("AUTRE", "Autre"),
    ]

    entreprise = models.OneToOneField(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="param_sms"
    )

    fournisseur = models.CharField(max_length=30, choices=FOURNISSEUR_CHOICES, default="BREVO")
    api_key = models.CharField(max_length=255, blank=True)
    sender_name = models.CharField(max_length=50, blank=True)
    sms_actif = models.BooleanField(default=False)

    modele_creation = models.TextField(blank=True)
    modele_arrivee = models.TextField(blank=True)
    modele_livraison = models.TextField(blank=True)
    modele_transfert = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entreprise__nom"]
        verbose_name = "Paramétrage SMS"
        verbose_name_plural = "Paramétrages SMS"

    def __str__(self):
        return f"SMS - {self.entreprise.nom}"


class HistoriqueAction(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Création"),
        ("UPDATE", "Modification"),
        ("DELETE", "Suppression"),
        ("LOGIN", "Connexion"),
        ("LOGOUT", "Déconnexion"),
        ("OTHER", "Autre"),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiques_actions"
    )
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiques_actions"
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default="OTHER")
    module = models.CharField(max_length=100)
    objet = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_action"]
        verbose_name = "Historique d'action"
        verbose_name_plural = "Historique des actions"

    def __str__(self):
        return f"{self.get_action_display()} - {self.module} - {self.objet}"

class RapportConnexion(models.Model):
    STATUT_CHOICES = [
        ("CONNECTE", "Connecté"),
        ("DECONNECTE", "Déconnecté"),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rapports_connexions"
    )
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rapports_connexions"
    )
    agence = models.ForeignKey(
        Agence,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rapports_connexions"
    )

    username_snapshot = models.CharField(max_length=150, blank=True)
    nom_complet_snapshot = models.CharField(max_length=255, blank=True)

    date_connexion = models.DateTimeField()
    date_deconnexion = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="CONNECTE")

    class Meta:
        ordering = ["-date_connexion"]
        verbose_name = "Rapport de connexion"
        verbose_name_plural = "Rapports de connexion"

    def __str__(self):
        return f"{self.username_snapshot or self.utilisateur} - {self.date_connexion}"

    @property
    def duree_session(self):
        if self.date_connexion and self.date_deconnexion:
            return self.date_deconnexion - self.date_connexion
        return None

class FactureClient(models.Model):
    TYPE_CHOICES = [
        ("ABONNEMENT", "Abonnement"),
        ("RENOUVELLEMENT", "Renouvellement"),
        ("SERVICE", "Service"),
        ("AUTRE", "Autre"),
    ]

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("EMISE", "Émise"),
        ("PAYEE", "Payée"),
        ("PARTIEL", "Paiement partiel"),
        ("ANNULEE", "Annulée"),
    ]

    numero = models.CharField(max_length=30, unique=True, blank=True)
    entreprise = models.ForeignKey(
        EntrepriseCliente,
        on_delete=models.CASCADE,
        related_name="factures"
    )

    type_facture = models.CharField(max_length=20, choices=TYPE_CHOICES, default="ABONNEMENT")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")

    date_emission = models.DateField()
    date_echeance = models.DateField(null=True, blank=True)

    periode_debut = models.DateField(null=True, blank=True)
    periode_fin = models.DateField(null=True, blank=True)

    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    devise = models.CharField(max_length=10, default="EUR")
    mode_paiement = models.CharField(max_length=50, blank=True)

    description = models.TextField(blank=True)
    observations = models.TextField(blank=True)

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administration_factures_clients_creees"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_emission", "-id"]
        verbose_name = "Facture client"
        verbose_name_plural = "Factures clients"

    def __str__(self):
        return self.numero or f"Facture {self.pk}"

    def save(self, *args, **kwargs):
        if not self.numero:
            dernier_id = (FactureClient.objects.order_by("-id").first().id + 1) if FactureClient.objects.exists() else 1
            self.numero = f"FAC{dernier_id:05d}"

        self.montant_ttc = (self.montant_ht or 0) + (self.tva or 0)
        super().save(*args, **kwargs)