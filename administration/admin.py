from django.contrib import admin
from .models import (
    Agence,
    EntrepriseCliente,
    FactureClient,
    HistoriqueAction,
    Parametre,
    ParametreSMS,
    ProfilAgent,
    RapportConnexion,
    VilleLivraison,
)

@admin.register(EntrepriseCliente)
class EntrepriseClienteAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "telephone", "email", "ville", "pays", "actif")
    list_filter = ("actif", "pays", "ville")
    search_fields = ("nom", "code", "telephone", "email", "ville", "adresse")
    ordering = ("nom",)


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = (
        "libelle",
        "cle",
        "entreprise",
        "categorie",
        "valeur",
        "type_valeur",
        "modifiable",
        "actif",
    )
    list_filter = ("categorie", "type_valeur", "modifiable", "actif", "entreprise")
    search_fields = ("libelle", "cle", "valeur", "description")
    ordering = ("entreprise", "categorie", "ordre", "libelle")


@admin.register(Agence)
class AgenceAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "entreprise", "ville", "telephone", "type_agence", "actif")
    list_filter = ("entreprise", "type_agence", "actif", "ville")
    search_fields = ("nom", "code", "ville", "telephone", "email", "responsable")
    ordering = ("entreprise", "nom")


@admin.register(ProfilAgent)
class ProfilAgentAdmin(admin.ModelAdmin):
    list_display = ("user", "entreprise", "agence", "role", "telephone", "actif")
    list_filter = ("entreprise", "agence", "role", "actif")
    search_fields = ("user__username", "user__first_name", "user__last_name", "telephone")
    ordering = ("entreprise", "user__username")

@admin.register(VilleLivraison)
class VilleLivraisonAdmin(admin.ModelAdmin):
    list_display = ("nom", "entreprise", "pays", "zone", "frais_livraison", "delai_estime_jours", "actif")
    list_filter = ("entreprise", "pays", "zone", "actif")
    search_fields = ("nom", "entreprise__nom", "pays", "zone")
    ordering = ("entreprise", "nom")


@admin.register(ParametreSMS)
class ParametreSMSAdmin(admin.ModelAdmin):
    list_display = ("entreprise", "fournisseur", "sender_name", "sms_actif")
    list_filter = ("fournisseur", "sms_actif")
    search_fields = ("entreprise__nom", "sender_name", "api_key")
    ordering = ("entreprise",)


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display = ("date_action", "utilisateur", "entreprise", "action", "module", "objet", "ip_address")
    list_filter = ("action", "module", "entreprise", "date_action")
    search_fields = ("objet", "description", "module", "utilisateur__username")
    ordering = ("-date_action",)

@admin.register(RapportConnexion)
class RapportConnexionAdmin(admin.ModelAdmin):
    list_display = (
        "date_connexion",
        "date_deconnexion",
        "username_snapshot",
        "entreprise",
        "agence",
        "statut",
        "ip_address",
    )
    list_filter = ("statut", "entreprise", "agence", "date_connexion")
    search_fields = ("username_snapshot", "nom_complet_snapshot", "ip_address", "user_agent")
    ordering = ("-date_connexion",)


@admin.register(FactureClient)
class FactureClientAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "entreprise",
        "type_facture",
        "statut",
        "date_emission",
        "date_echeance",
        "montant_ttc",
        "devise",
    )
    list_filter = ("type_facture", "statut", "devise", "entreprise")
    search_fields = ("numero", "entreprise__nom", "description", "observations")
    ordering = ("-date_emission", "-id")