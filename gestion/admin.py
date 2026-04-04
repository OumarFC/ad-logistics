from django.contrib import admin
from .models import Ballon, BallonItem
from .models import Client

# Register your models here.
from .models import ColisRecu
from .models import Facture, ParametreFacture, PaiementFacture, HistoriqueEnvoiFacture

@admin.register(ColisRecu)
class ColisRecuAdmin(admin.ModelAdmin):
    list_display = ("reference", "expediteur_nom", "destinataire_nom", "date_enregistrement", "restant_euros", "nbs", "statut")
    search_fields = ("reference", "expediteur_nom", "destinataire_nom", "expediteur_tel", "destinataire_tel")
    list_filter = ("statut", "date_enregistrement", "livraison", "type_colis")


class BallonItemInline(admin.TabularInline):
    model = BallonItem
    extra = 0

@admin.register(Ballon)
class BallonAdmin(admin.ModelAdmin):
    list_display = ("code","type_ballon","agence_destination","created_at","statut")
    search_fields = ("code",)
    list_filter = ("type_ballon","agence_destination","statut")
    inlines = [BallonItemInline]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email")
    search_fields = ("nom", "telephone")


@admin.register(ParametreFacture)
class ParametreFactureAdmin(admin.ModelAdmin):
    list_display = ("nom_entreprise", "telephone", "email", "devise_defaut", "date_modification")


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = (
        "numero", "type_piece", "ref_colis", "exp_nom", "des_nom",
        "date_facture", "montant_ttc", "devise", "statut"
    )
    list_filter = ("type_piece", "statut", "devise", "date_facture")
    search_fields = ("numero", "ref_colis", "exp_nom", "des_nom", "exp_tel", "des_tel")


@admin.register(PaiementFacture)
class PaiementFactureAdmin(admin.ModelAdmin):
    list_display = ("facture", "date_paiement", "montant", "mode_paiement", "created_at")


@admin.register(HistoriqueEnvoiFacture)
class HistoriqueEnvoiFactureAdmin(admin.ModelAdmin):
    list_display = ("facture", "email_destinataire", "succes", "created_at")