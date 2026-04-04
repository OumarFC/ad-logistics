from django.db import models
import random
from django.db import IntegrityError
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from django.utils import timezone

# -------- Colis reçus --------

class ColisRecu(models.Model):

    STATUT_PRISE_EN_CHARGE = "PEC"
    STATUT_EN_COURS = "ECR"
    STATUT_ARRIVEE = "ARR"
    STATUT_LIVR = "LIVR"

    STATUT_CHOICES = [
        ("PEC", "Pris en charge"),
        ("ECR", "En cours"),
        ("ARR", "Arrivée"),
        ("LIVR", "Livré"),
    ]
    
    TYPE_FRET_CHOICES = [
        ("AERIEN", "Fret aérien"),
        ("MARITIME", "Fret maritime"),
    ]


    reference = models.CharField(max_length=6, unique=True, blank=True)   # ex: AD1934
    statut = models.CharField(max_length=4, choices=STATUT_CHOICES, default="PEC")
    livraison = models.BooleanField(default=False)
    type_fret = models.CharField(max_length=10, choices=TYPE_FRET_CHOICES, default="AERIEN")

    expediteur_nom = models.CharField(max_length=120)
    expediteur_tel = models.CharField(max_length=32, blank=True)
    expediteur_adresse = models.CharField(max_length=120, blank=True)

    destinataire_nom = models.CharField(max_length=120)
    destinataire_tel = models.CharField(max_length=32, blank=True)
    agence_destination = models.CharField(max_length=120, blank=True)

    agent_nom = models.CharField(max_length=120, blank=True)

    date_enregistrement = models.DateField()
    poids_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prix_fret_euros = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    restant_euros = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)

    nb_colis_total = models.PositiveIntegerField(default=1)
    nbs = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=250, blank=True)
    type_colis = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_enregistrement", "-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.expediteur_nom}"

    def compute_prix(self):
        poids = self.poids_kg or Decimal("0")
        if poids <= 0:
            return Decimal("0.00")
        tarif = Decimal("12.00") if self.type_fret == "AERIEN" else Decimal("4.00")
        return (poids * tarif).quantize(Decimal("0.01"))

    def generate_reference(self):
        prefix = "AD"
        while True:
            ref = f"{prefix}{random.randint(0, 9999):04d}"   # AD1934
            if not ColisRecu.objects.filter(reference=ref).exists():
                return ref

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()

        if not self.nb_colis_total or self.nb_colis_total < 1:
            self.nb_colis_total = 1

        self.prix_fret_euros = self.compute_prix()
        super().save(*args, **kwargs)
        
# -------- Colis envoyés --------
class ColisEnvoye(models.Model):
    STATUT_CHOICES = [
        ("OK", "OK"),
        ("ATT", "À vérifier"),
        ("LIVR", "Livré"),
    ]
    reference = models.CharField(max_length=64, unique=True)
    statut = models.CharField(max_length=4, choices=STATUT_CHOICES, default="ATT")

    expediteur_nom = models.CharField(max_length=120)
    expediteur_tel = models.CharField(max_length=32, blank=True)
    destinataire_nom = models.CharField(max_length=120)
    destinataire_tel = models.CharField(max_length=32, blank=True)

    prix_euros = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    type_colis = models.CharField(max_length=64, blank=True)
    poids_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_envoi = models.DateField()
    description = models.CharField(max_length=250, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_envoi", "-created_at"]

    def __str__(self):
        return f"ENVOYE {self.reference}"


# -------- Factures / Devis --------
# -------- Paramètres template facture / devis / avoir --------
class ParametreFacture(models.Model):
    """
    Paramètres généraux de facturation, personnalisables par entreprise.
    Si plus tard tu rends le système multi-client complet, remplace simplement
    par une FK vers EntrepriseCliente au lieu d'une config unique.
    """
    nom_entreprise = models.CharField(max_length=150, default="AD Logistics")
    sous_titre = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="parametres/factures/", blank=True, null=True)

    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.CharField(max_length=255, blank=True)

    devise_defaut = models.CharField(max_length=8, default="EUR")
    taux_tva_defaut = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    delai_paiement_jours = models.PositiveIntegerField(default=7)

    prefixe_facture = models.CharField(max_length=20, default="FAC")
    prefixe_devis = models.CharField(max_length=20, default="DEV")
    prefixe_avoir = models.CharField(max_length=20, default="AV")

    prochain_numero_facture = models.PositiveIntegerField(default=1)
    prochain_numero_devis = models.PositiveIntegerField(default=1)
    prochain_numero_avoir = models.PositiveIntegerField(default=1)

    iban = models.CharField(max_length=80, blank=True)
    bic = models.CharField(max_length=50, blank=True)

    texte_entete = models.TextField(blank=True)
    conditions_reglement = models.TextField(blank=True)
    pied_facture = models.TextField(blank=True)

    modele_email_sujet = models.CharField(
        max_length=255,
        default="Votre {type_piece} {numero} - {entreprise}"
    )
    modele_email_message = models.TextField(
        default=(
            "Bonjour {client_nom},\n\n"
            "Veuillez trouver ci-joint votre {type_piece} {numero} "
            "relatif(ve) au colis {ref_colis}.\n\n"
            "Montant total : {total_ttc} {devise}\n\n"
            "Cordialement,\n"
            "{entreprise}"
        )
    )

    couleur_primaire = models.CharField(max_length=20, default="#0f172a")

    afficher_logo = models.BooleanField(default=True)
    afficher_iban_bic = models.BooleanField(default=True)
    afficher_conditions = models.BooleanField(default=True)
    afficher_bloc_expediteur = models.BooleanField(default=True)
    afficher_bloc_destinataire = models.BooleanField(default=True)

    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramètre de facturation"
        verbose_name_plural = "Paramètres de facturation"

    def __str__(self):
        return self.nom_entreprise


# -------- Factures / Devis / Avoir --------
class Facture(models.Model):
    QUI_PAYE_CHOICES = [
        ("EXP", "Expéditeur"),
        ("DES", "Destinataire"),
        ("AUT", "Autre"),
    ]

    TYPE_CHOICES = [
        ("FACTURE", "FACTURE"),
        ("DEVIS", "DEVIS"),
        ("AVOIR", "AVOIR"),
    ]

    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("VALIDE", "Validé"),
        ("ENVOYEE", "Envoyée"),
        ("PARTIEL", "Partiellement payée"),
        ("PAYEE", "Payée"),
        ("RETARD", "En retard"),
        ("ANNULEE", "Annulée"),
    ]

    # Référence documentaire
    numero = models.CharField("Numéro", max_length=50, unique=True, blank=True)
    type_piece = models.CharField("TYPE", max_length=16, choices=TYPE_CHOICES, default="FACTURE")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="BROUILLON")

    # Optionnel : liaison vers ton modèle Fret / ColisRecu si besoin
    # colis = models.ForeignKey(
    #     "ColisRecu",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="factures"
    # )

    # Expéditeur
    exp_tel = models.CharField("Téléphone expéditeur", max_length=32, blank=True)
    exp_nom = models.CharField("Nom expéditeur", max_length=120)
    exp_prenom = models.CharField("Prénom expéditeur", max_length=120, blank=True)
    exp_mail = models.EmailField("Mail expéditeur", blank=True)
    exp_adresse = models.CharField("Adresse postale expéditeur", max_length=200, blank=True)

    # Destinataire
    des_tel = models.CharField("Téléphone destinataire", max_length=32, blank=True)
    des_nom = models.CharField("Nom destinataire", max_length=120)
    des_prenom = models.CharField("Prénom destinataire", max_length=120, blank=True)
    des_mail = models.EmailField("Mail destinataire", blank=True)
    des_adresse = models.CharField("Adresse postale destinataire", max_length=200, blank=True)
    des_agence = models.CharField("Agence destination", max_length=120, blank=True)
    livraison = models.BooleanField("Livraison", default=False)

    # Infos colis / fret
    description = models.CharField("Description", max_length=250, blank=True)
    produit = models.CharField("Produit / référence", max_length=120, blank=True)
    ref_colis = models.CharField("Réf colis", max_length=64, db_index=True)
    date_colis = models.DateField("Date colis")

    poids_kg = models.DecimalField("Poids (kg)", max_digits=10, decimal_places=2, default=Decimal("0.00"))
    nb_colis = models.PositiveIntegerField("Nombre de colis", default=1)

    # Facturation
    qui_paye = models.CharField("Qui paye ?", max_length=3, choices=QUI_PAYE_CHOICES, default="EXP")
    devise = models.CharField("Devise", max_length=8, default="EUR")

    montant_ht = models.DecimalField("Montant HT", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    taux_tva = models.DecimalField("TVA (%)", max_digits=5, decimal_places=2, default=Decimal("0.00"))
    montant_tva = models.DecimalField("Montant TVA", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    remise = models.DecimalField("Remise", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    montant_ttc = models.DecimalField("Montant TTC", max_digits=12, decimal_places=2, default=Decimal("0.00"))

    montant_paye = models.DecimalField("Montant payé", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reste_a_payer = models.DecimalField("Reste à payer", max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # Dates de gestion
    date_facture = models.DateField("Date facture", default=timezone.localdate)
    date_echeance = models.DateField("Date échéance", blank=True, null=True)
    date_envoi_email = models.DateTimeField("Date envoi e-mail", blank=True, null=True)
    date_paiement = models.DateField("Date paiement", blank=True, null=True)

    # Notes
    note_client = models.TextField("Note client", blank=True)
    note_interne = models.TextField("Note interne", blank=True)

    # Métadonnées
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gestion_factures_creees"
    )

    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gestion_factures_modifiees"
    )
    
    pdf_archive = models.FileField(
    "PDF archivé",
    upload_to="factures/pdf/",
    blank=True,
    null=True
    )

    qr_code_image = models.ImageField(
        "QR code",
        upload_to="factures/qrcodes/",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_facture", "-created_at"]
        verbose_name = "Facture / Devis / Avoir"
        verbose_name_plural = "Factures / Devis / Avoir"

    def __str__(self):
        return f"{self.type_piece} {self.numero or self.ref_colis} ({self.montant_ttc} {self.devise})"

    @property
    def client_nom_complet(self):
        if self.qui_paye == "DES":
            return f"{self.des_nom} {self.des_prenom}".strip()
        return f"{self.exp_nom} {self.exp_prenom}".strip()

    @property
    def client_email_facturation(self):
        if self.qui_paye == "DES":
            return self.des_mail
        return self.exp_mail

    def calculer_totaux(self):
        ht = self.montant_ht or Decimal("0.00")
        remise = self.remise or Decimal("0.00")
        taux_tva = self.taux_tva or Decimal("0.00")
        montant_paye = self.montant_paye or Decimal("0.00")

        base_ht = max(ht - remise, Decimal("0.00"))
        tva = (base_ht * taux_tva) / Decimal("100.00")
        ttc = base_ht + tva
        reste = max(ttc - montant_paye, Decimal("0.00"))

        self.montant_tva = tva
        self.montant_ttc = ttc
        self.reste_a_payer = reste

        # Mise à jour auto du statut, sauf cas bloqués
        if self.statut not in ["BROUILLON", "ANNULEE"]:
            today = timezone.localdate()
            if ttc > 0 and reste == 0:
                self.statut = "PAYEE"
                if not self.date_paiement:
                    self.date_paiement = today
            elif montant_paye > 0:
                self.statut = "PARTIEL"
            elif self.date_echeance and self.date_echeance < today:
                self.statut = "RETARD"
            elif self.statut == "BROUILLON":
                self.statut = "VALIDE"

    def save(self, *args, **kwargs):
        # Préremplissage date échéance si absente
        if not self.date_echeance:
            params = ParametreFacture.objects.first()
            delai = params.delai_paiement_jours if params else 7
            self.date_echeance = self.date_facture + timezone.timedelta(days=delai)

        # Numérotation auto
        if not self.numero:
            self.numero = self.generer_numero()

        self.calculer_totaux()
        super().save(*args, **kwargs)

    def generer_numero(self):
        params = ParametreFacture.objects.first()

        if not params:
            # secours minimal si les paramètres n'existent pas encore
            year = timezone.now().year
            last_id = (Facture.objects.order_by("-id").first().id + 1) if Facture.objects.exists() else 1
            return f"{self.type_piece[:3]}-{year}-{last_id:04d}"

        year = timezone.now().year

        if self.type_piece == "FACTURE":
            numero = f"{params.prefixe_facture}-{year}-{params.prochain_numero_facture:04d}"
            params.prochain_numero_facture += 1
            params.save(update_fields=["prochain_numero_facture"])
            return numero

        if self.type_piece == "DEVIS":
            numero = f"{params.prefixe_devis}-{year}-{params.prochain_numero_devis:04d}"
            params.prochain_numero_devis += 1
            params.save(update_fields=["prochain_numero_devis"])
            return numero

        numero = f"{params.prefixe_avoir}-{year}-{params.prochain_numero_avoir:04d}"
        params.prochain_numero_avoir += 1
        params.save(update_fields=["prochain_numero_avoir"])
        return numero

class PaiementFacture(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ("ESPECES", "Espèces"),
        ("VIREMENT", "Virement"),
        ("CB", "Carte bancaire"),
        ("CHEQUE", "Chèque"),
        ("MOBILE", "Mobile Money"),
        ("AUTRE", "Autre"),
    ]

    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name="paiements"
    )
    date_paiement = models.DateField(default=timezone.localdate)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default="ESPECES")
    reference_paiement = models.CharField(max_length=100, blank=True)
    commentaire = models.TextField(blank=True)

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_paiement", "-created_at"]

    def __str__(self):
        return f"{self.facture.numero} - {self.montant} {self.facture.devise}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        facture = self.facture
        total_paye = facture.paiements.aggregate(
            total=models.Sum("montant")
        )["total"] or Decimal("0.00")

        facture.montant_paye = total_paye
        facture.calculer_totaux()
        facture.save(update_fields=[
            "montant_paye",
            "montant_tva",
            "montant_ttc",
            "reste_a_payer",
            "statut",
            "date_paiement",
            "updated_at",
        ])
  
class HistoriqueEnvoiFacture(models.Model):
    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name="envois_email"
    )
    email_destinataire = models.TextField()
    sujet = models.CharField(max_length=255)
    message = models.TextField(blank=True)

    succes = models.BooleanField(default=False)
    erreur = models.TextField(blank=True)

    envoye_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.facture.numero} -> {self.email_destinataire}"
        
# -------- Journal comptable --------
class OperationComptable(models.Model):
    SENS_CHOICES   = [("ENTREE", "Entrée"), ("SORTIE", "Sortie")]
    MODE_CHOICES   = [("ESPECES", "Espèces"), ("BANQUE", "Banque"), ("AUTRE", "Autre")]
    AGENCE_CHOICES = [("PARIS", "PARIS"), ("ROISSY", "ROISSY")]

    date = models.DateField()
    libelle = models.CharField(max_length=160)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    sens = models.CharField(max_length=6, choices=SENS_CHOICES)
    mode = models.CharField(max_length=8, choices=MODE_CHOICES, default="ESPECES")
    agence = models.CharField(max_length=20, choices=AGENCE_CHOICES, default="PARIS")
    ref_colis = models.CharField(max_length=64, blank=True)
    utilisateur = models.CharField(max_length=80, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} {self.sens} {self.montant} {self.libelle}"

class Ballon(models.Model):
    TYPE_CHOICES = [("23KG", "BALLON 23 KG"), ("32KG", "BALLON 32 KG")]
    AGENCES = [("PARIS", "PARIS AGENCE"), ("MATOTO", "MATOTO"), ("ROISSY", "ROISSY")]

    code = models.CharField(max_length=32, unique=True, help_text="Ex: BAL001, BAL B3, etc.")
    type_ballon = models.CharField(max_length=5, choices=TYPE_CHOICES, default="23KG")
    agence_destination = models.CharField(max_length=20, choices=AGENCES, default="PARIS")
    commentaire = models.CharField(max_length=200, blank=True)
    statut = models.CharField(max_length=20, default="EN PRÉPA")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({self.get_type_ballon_display()})"


class BallonItem(models.Model):
    ballon = models.ForeignKey(Ballon, on_delete=models.CASCADE, related_name="items")
    reference = models.CharField(max_length=64)       # BA1176-1, etc.
    poids_kg = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "id"]

    def __str__(self):
        return f"{self.reference} ({self.poids_kg} kg)"

class SMSMessage(models.Model):
    titre = models.CharField(max_length=120)
    message = models.TextField()
    liste_telephones = models.TextField(
        help_text="Liste séparée par ';' ex: 07000000;07111111;07222222"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.titre


class TransfertArgent(models.Model):
    DEVISE_CHOICES = [
        ("EUR", "Euro"),
        ("GNF", "Franc guinéen"),
    ]

    STATUT_CHOICES = [
        ("ATT", "À vérifier"),
        ("OK", "En cours"),
        ("PAYE", "Retiré"),
        ("ANN", "Annulé"),
    ]

    FRAIS_POURCENTAGE_CHOICES = [
        (Decimal("1.0"), "1%"),
        (Decimal("1.5"), "1,5%"),
        (Decimal("2.0"), "2%"),
        (Decimal("2.5"), "2,5%"),
        (Decimal("3.0"), "3%"),
        (Decimal("3.5"), "3,5%"),
        (Decimal("4.0"), "4%"),
        (Decimal("4.5"), "4,5%"),
        (Decimal("5.0"), "5%"),
    ]

    reference = models.CharField(max_length=6, unique=True, blank=True)   # ex AD5821
    statut = models.CharField(max_length=4, choices=STATUT_CHOICES, default="ATT")

    agent_nom = models.CharField(max_length=120, blank=True)

    expediteur_nom = models.CharField(max_length=120)
    expediteur_tel = models.CharField(max_length=32, blank=True)

    destinataire_nom = models.CharField(max_length=120)
    destinataire_tel = models.CharField(max_length=32, blank=True)

    devise_envoi = models.CharField(max_length=3, choices=DEVISE_CHOICES, default="EUR")
    montant_envoye = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # TAUX DE TRANSFERT (différent du frais)
    taux_transfert = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # FRAIS
    frais_pourcentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        choices=FRAIS_POURCENTAGE_CHOICES,
        blank=True,
        null=True
    )
    frais_transfert = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # TOTAL À PAYER PAR LE CLIENT / EXPEDITEUR
    montant_total_payer = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    devise_reception = models.CharField(max_length=3, choices=DEVISE_CHOICES, default="GNF")
    montant_reception = models.DecimalField(max_digits=14, decimal_places=2, default=0, blank=True)

    date_transfert = models.DateField()
    date_retrait = models.DateField(blank=True, null=True)

    description = models.CharField(max_length=250, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_transfert", "-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.expediteur_nom} -> {self.destinataire_nom}"

    def generate_reference(self):
        prefix = "AD"
        while True:
            ref = f"{prefix}{random.randint(0, 9999):04d}"
            if not TransfertArgent.objects.filter(reference=ref).exists():
                return ref

    def get_default_frais_pourcentage(self):
        montant = self.montant_envoye or Decimal("0")

        if montant >= Decimal("1") and montant <= Decimal("999"):
            return Decimal("4.0")
        elif montant >= Decimal("1000"):
            return Decimal("3.0")
        return Decimal("0.0")

    def compute_frais_transfert(self):
        montant = self.montant_envoye or Decimal("0")

        pourcentage = self.frais_pourcentage
        if pourcentage is None:
            pourcentage = self.get_default_frais_pourcentage()

        if montant <= 0 or pourcentage <= 0:
            return Decimal("0.00")

        frais = (montant * pourcentage / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        return frais

    def compute_montant_total_payer(self):
        montant = self.montant_envoye or Decimal("0")
        frais = self.frais_transfert or Decimal("0")
        return (montant + frais).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def compute_montant_reception(self):
        montant = self.montant_envoye or Decimal("0")
        taux = self.taux_transfert or Decimal("0")

        if montant <= 0 or taux <= 0:
            return Decimal("0.00")

        if self.devise_envoi == "EUR" and self.devise_reception == "GNF":
            return (montant * taux).quantize(Decimal("0.01"))

        if self.devise_envoi == "GNF" and self.devise_reception == "EUR":
            return (montant / taux).quantize(Decimal("0.01"))

        return montant.quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()

        if self.frais_pourcentage is None:
            self.frais_pourcentage = self.get_default_frais_pourcentage()

        self.frais_transfert = self.compute_frais_transfert()
        self.montant_total_payer = self.compute_montant_total_payer()
        self.montant_reception = self.compute_montant_reception()

        super().save(*args, **kwargs)

class SMSLog(models.Model):
    STATUT_CHOICES = [
        ("success", "Succès"),
        ("error", "Erreur"),
    ]

    numero = models.CharField(max_length=30)
    client_nom = models.CharField(max_length=150, blank=True, null=True)
    message = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="success")
    provider = models.CharField(max_length=50, default="brevo")
    provider_message_id = models.CharField(max_length=100, blank=True, null=True)
    erreur = models.TextField(blank=True, null=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sms_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.numero} - {self.statut}"


class Client(models.Model):
    nom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30)

    # optionnel mais recommandé
    email = models.EmailField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.telephone})"
