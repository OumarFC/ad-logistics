from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import localdate, now
from django.db.models import Sum, Case, When, DecimalField, Q, F
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import ColisRecu, ColisEnvoye, Facture, OperationComptable
from .forms import ColisRecuForm, ColisEnvoyeForm, FactureForm, DevisForm, BilanFilterForm
from itertools import chain
from django.db.models import Value, CharField
import csv
from django.urls import reverse
from .models import SMSMessage
from .forms import SMSMessageForm
from .models import Ballon, BallonItem
from .forms import BallonForm, BallonItemForm
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from .models import TransfertArgent,SMSLog
from .forms import TransfertArgentForm
import qrcode
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from .forms_sms import EnvoyerSMSForm
from .services.sms_service import send_sms_brevo, SMSServiceError, build_fret_status_sms, send_fret_status_sms_if_enabled

from django.core.mail import EmailMessage

from .models import HistoriqueEnvoiFacture, ParametreFacture
from .utils_facture import render_facture_pdf_bytes

from .forms import FactureEmailForm
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .utils_facture import archive_facture_pdf, ensure_facture_qrcode

def get_named_period_dates(request, prefix):
    today = timezone.localdate()
    period = request.GET.get(f"{prefix}_periode", "jour")

    date_from = None
    date_to = None

    if period == "jour":
        date_from = today
        date_to = today

    elif period == "semaine":
        date_from = today - timedelta(days=today.weekday())
        date_to = date_from + timedelta(days=6)

    elif period == "mois":
        date_from = today.replace(day=1)
        if date_from.month == 12:
            next_month = date_from.replace(year=date_from.year + 1, month=1, day=1)
        else:
            next_month = date_from.replace(month=date_from.month + 1, day=1)
        date_to = next_month - timedelta(days=1)

    elif period == "libre":
        du = request.GET.get(f"{prefix}_du")
        au = request.GET.get(f"{prefix}_au")

        if du:
            try:
                date_from = datetime.strptime(du, "%Y-%m-%d").date()
            except ValueError:
                date_from = None

        if au:
            try:
                date_to = datetime.strptime(au, "%Y-%m-%d").date()
            except ValueError:
                date_to = None

    return period, date_from, date_to
    

def get_period_dates(request):
    today = timezone.localdate()
    period = request.GET.get("periode", "jour")

    date_from = None
    date_to = None

    if period == "jour":
        date_from = today
        date_to = today

    elif period == "semaine":
        date_from = today - timedelta(days=today.weekday())
        date_to = date_from + timedelta(days=6)

    elif period == "mois":
        date_from = today.replace(day=1)
        if date_from.month == 12:
            next_month = date_from.replace(year=date_from.year + 1, month=1, day=1)
        else:
            next_month = date_from.replace(month=date_from.month + 1, day=1)
        date_to = next_month - timedelta(days=1)

    elif period == "libre":
        du = request.GET.get("bilan_du")
        au = request.GET.get("bilan_au")

        if du:
            try:
                date_from = date.fromisoformat(du)
            except ValueError:
                date_from = None

        if au:
            try:
                date_to = date.fromisoformat(au)
            except ValueError:
                date_to = None

    return period, date_from, date_to
    
def apply_date_filter(queryset, field_name, date_from, date_to):
    filters = {}
    if date_from:
        filters[f"{field_name}__gte"] = date_from
    if date_to:
        filters[f"{field_name}__lte"] = date_to
    return queryset.filter(**filters)
    
def get_fret_bilan(colis_qs):
    return colis_qs.aggregate(
        nb_operations=Count("id"),
        total_prix_fret=Coalesce(Sum("prix_fret_euros"), Decimal("0.00")),
        total_restant=Coalesce(Sum("restant_euros"), Decimal("0.00")),
        total_poids=Coalesce(Sum("poids_kg"), Decimal("0.00")),
        total_nb_colis=Coalesce(Sum("nb_colis_total"), 0),
    )
 
def get_transfert_bilan(transfert_qs):
    return transfert_qs.aggregate(
        nb_operations=Count("id"),
        total_envoye=Coalesce(Sum("montant_envoye"), Decimal("0.00")),
        total_frais=Coalesce(Sum("frais_transfert"), Decimal("0.00")),
        total_a_payer=Coalesce(Sum("montant_total_payer"), Decimal("0.00")),
        total_a_recevoir=Coalesce(Sum("montant_reception"), Decimal("0.00")),
    )


def get_period_dates(request):
    today = timezone.localdate()
    period = request.GET.get("periode", "jour")

    date_from = None
    date_to = None

    if period == "jour":
        date_from = today
        date_to = today

    elif period == "semaine":
        date_from = today - timedelta(days=today.weekday())
        date_to = date_from + timedelta(days=6)

    elif period == "mois":
        date_from = today.replace(day=1)
        if date_from.month == 12:
            next_month = date_from.replace(year=date_from.year + 1, month=1, day=1)
        else:
            next_month = date_from.replace(month=date_from.month + 1, day=1)
        date_to = next_month - timedelta(days=1)

    elif period == "libre":
        du = request.GET.get("bilan_du")
        au = request.GET.get("bilan_au")

        if du:
            try:
                date_from = datetime.strptime(du, "%Y-%m-%d").date()
            except ValueError:
                date_from = None

        if au:
            try:
                date_to = datetime.strptime(au, "%Y-%m-%d").date()
            except ValueError:
                date_to = None

    return period, date_from, date_to


def apply_date_filter(queryset, field_name, date_from, date_to):
    filters = {}
    if date_from:
        filters[f"{field_name}__gte"] = date_from
    if date_to:
        filters[f"{field_name}__lte"] = date_to
    return queryset.filter(**filters)
    

def get_fret_bilan(queryset):
    return queryset.aggregate(
        nb_operations=Count("id"),
        total_prix_fret=Coalesce(Sum("prix_fret_euros"), Decimal("0.00")),
        total_restant=Coalesce(Sum("restant_euros"), Decimal("0.00")),
        total_poids=Coalesce(Sum("poids_kg"), Decimal("0.00")),
        total_nb_colis=Coalesce(Sum("nb_colis_total"), 0),
    )
    
def get_transfert_bilan(queryset):
    return queryset.aggregate(
        nb_operations=Count("id"),
        total_envoye=Coalesce(Sum("montant_envoye"), Decimal("0.00")),
        total_frais=Coalesce(Sum("frais_transfert"), Decimal("0.00")),
        total_a_payer=Coalesce(Sum("montant_total_payer"), Decimal("0.00")),
        total_a_recevoir=Coalesce(Sum("montant_reception"), Decimal("0.00")),
    )

def get_transfert_sous_totaux(queryset):
    envoi_rows = (
        queryset.values("devise_envoi")
        .annotate(
            total_envoye=Coalesce(Sum("montant_envoye"), Decimal("0.00")),
            total_frais=Coalesce(Sum("frais_transfert"), Decimal("0.00")),
            total_a_payer=Coalesce(Sum("montant_total_payer"), Decimal("0.00")),
            nb_operations=Count("id"),
        )
        .order_by("devise_envoi")
    )

    reception_rows = (
        queryset.values("devise_reception")
        .annotate(
            total_a_recevoir=Coalesce(Sum("montant_reception"), Decimal("0.00")),
            nb_operations=Count("id"),
        )
        .order_by("devise_reception")
    )

    return {
        "envoi": list(envoi_rows),
        "reception": list(reception_rows),
    }
    

def build_bilan_context(request):
    period, date_from, date_to = get_period_dates(request)

    fret_qs = ColisRecu.objects.all()
    fret_qs = apply_date_filter(fret_qs, "date_enregistrement", date_from, date_to)

    transfert_qs = TransfertArgent.objects.all()
    transfert_qs = apply_date_filter(transfert_qs, "date_transfert", date_from, date_to)

    fret_bilan = get_fret_bilan(fret_qs)
    transfert_bilan = get_transfert_bilan(transfert_qs)
    transfert_sous_totaux = get_transfert_sous_totaux(transfert_qs)

    return {
        "bilan_period": period,
        "bilan_du": date_from,
        "bilan_au": date_to,
        "fret_bilan": fret_bilan,
        "transfert_bilan": transfert_bilan,
        "transfert_sous_totaux": transfert_sous_totaux,
        "fret_bilan_list": fret_qs.order_by("-date_enregistrement", "-id")[:100],
        "transfert_bilan_list": transfert_qs.order_by("-date_transfert", "-created_at")[:100],
    }
 
def compute_bilan(request):
    # Filtres par défaut : 1er jour du mois courant -> aujourd’hui
    today = localdate()
    du = request.GET.get("du") or str(today.replace(day=1))
    au = request.GET.get("au") or str(today)
    agence = request.GET.get("agence") or ""

    # Chiffre d’affaires : uniquement FACTURE dans la période
    fact_q = Facture.objects.filter(type_piece="FACTURE", date_colis__range=[du, au])
    if agence:
        # Heuristique simple d'agence (adapte selon ton modèle réel)
        fact_q = fact_q.filter(Q(des_agence=agence) | Q(exp_adresse__icontains=agence))

    ca_exp = fact_q.filter(qui_paye="EXP").aggregate(s=Sum("montant"))["s"] or 0
    ca_des = fact_q.filter(qui_paye="DES").aggregate(s=Sum("montant"))["s"] or 0
    ca_aut = fact_q.filter(qui_paye="AUT").aggregate(s=Sum("montant"))["s"] or 0
    total_ca = ca_exp + ca_des + ca_aut

    # Journal comptable
    op_q = OperationComptable.objects.filter(date__range=[du, au])
    if agence:
        op_q = op_q.filter(agence=agence)
    agg = op_q.aggregate(
        entrees=Sum(Case(When(sens="ENTREE", then="montant"), default=0, output_field=DecimalField())),
        sorties=Sum(Case(When(sens="SORTIE", then="montant"), default=0, output_field=DecimalField())),
        especes=Sum(Case(When(mode="ESPECES", then="montant"), default=0, output_field=DecimalField())),
        banque=Sum(Case(When(mode="BANQUE",  then="montant"), default=0, output_field=DecimalField())),
    )
    entrees = agg["entrees"] or 0
    sorties = agg["sorties"] or 0
    total_especes = agg["especes"] or 0
    total_banque  = agg["banque"]  or 0

    # Listes d’illustration
    payes_par_exp = fact_q.filter(qui_paye="EXP").order_by("-date_colis")[:50]
    payes_par_des = fact_q.filter(qui_paye="DES").order_by("-date_colis")[:50]

    return {
        "filters": {"du": du, "au": au, "agence": agence},
        "kpis": {
            "total_exp": ca_exp, "total_des": ca_des, "total_autre": ca_aut, "total_ca": total_ca,
            "op_entrees": entrees, "op_sorties": sorties,
            "total_especes": total_especes, "total_banque": total_banque,
        },
        "ops": op_q.order_by("-date", "-id")[:50],
        "payes_par_exp": payes_par_exp,
        "payes_par_des": payes_par_des,
    }


# --- Helpers BILANS -----------------------------------------------------------

def _last_reset_date(request):
    """
    Renvoie la date du DERNIER 'vidange de caisse' si on en trouve une
    dans OperationComptable (libellé contient 'VIDANGE'), sinon le 1er jour du mois.
    Tu peux plus tard créer un bouton qui ajoute une OP 'VIDANGE'.
    """
    agence = request.GET.get("agence") or ""
    qs = OperationComptable.objects.filter(libelle__icontains="VIDANGE")
    if agence:
        qs = qs.filter(agence=agence)
    r = qs.order_by("-date", "-id").first()
    if r:
        return r.date
    # défaut = premier du mois courant
    t = localdate()
    return t.replace(day=1)

def _range_du_au(request):
    today = localdate()
    du = request.GET.get("du")
    au = request.GET.get("au")
    return (du or str(today.replace(day=1)), au or str(today))

def _compute_caisse_and_ca(request, du, au, agence):
    # CA sur FACTURE
    fact = Facture.objects.filter(type_piece="FACTURE", date_colis__range=[du, au])
    if agence:
        fact = fact.filter(Q(des_agence=agence) | Q(exp_adresse__icontains=agence))

    ca_exp = fact.filter(qui_paye="EXP").aggregate(s=Sum("montant"))["s"] or 0
    ca_des = fact.filter(qui_paye="DES").aggregate(s=Sum("montant"))["s"] or 0
    ca_aut = fact.filter(qui_paye="AUT").aggregate(s=Sum("montant"))["s"] or 0
    total_ca = ca_exp + ca_des + ca_aut

    # Journal comptable
    ops = OperationComptable.objects.filter(date__range=[du, au])
    if agence:
        ops = ops.filter(agence=agence)
    agg = ops.aggregate(
        entrees=Sum(Case(When(sens="ENTREE", then="montant"), default=0, output_field=DecimalField())),
        sorties=Sum(Case(When(sens="SORTIE", then="montant"), default=0, output_field=DecimalField())),
        especes=Sum(Case(When(mode="ESPECES", then="montant"), default=0, output_field=DecimalField())),
        banque=Sum(Case(When(mode="BANQUE",  then="montant"), default=0, output_field=DecimalField())),
    )
    return {
        "ca_exp": ca_exp, "ca_des": ca_des, "ca_aut": ca_aut, "total_ca": total_ca,
        "entrees": agg["entrees"] or 0, "sorties": agg["sorties"] or 0,
        "especes": agg["especes"] or 0, "banque": agg["banque"] or 0,
        "ops": ops.order_by("-date", "-id")[:100],
        "fact": fact,
    }

def compute_bilan(request):
    agence = request.GET.get("agence") or ""
    # bloc “TOTAL calculé depuis le dernier vidange”
    since_reset = _last_reset_date(request)
    sr = str(since_reset); today = str(localdate())
    bloc_reset = _compute_caisse_and_ca(request, sr, today, agence)

    # bloc “Afficher le bilan entre deux dates”
    du, au = _range_du_au(request)
    bloc_range = _compute_caisse_and_ca(request, du, au, agence)

    # listes “payés par … depuis le dernier vidange”
    payes_par_exp = bloc_reset["fact"].filter(qui_paye="EXP").order_by("-date_colis")[:50]
    payes_par_des = bloc_reset["fact"].filter(qui_paye="DES").order_by("-date_colis")[:50]

    return {
        "filters": {"du": du, "au": au, "agence": agence},
        "since_reset": since_reset,
        "reset": bloc_reset,    # chiffres de la 1ère carte
        "range": bloc_range,    # chiffres 2ème carte
        "ops": bloc_range["ops"],
        "payes_par_exp": payes_par_exp,
        "payes_par_des": payes_par_des,
    }

# --- Exports & Prints ---------------------------------------------------------

def export_paiements_csv(request):
    du, au = _range_du_au(request)
    agence = request.GET.get("agence") or ""
    data = _compute_caisse_and_ca(request, du, au, agence)
    fact = data["fact"]  # toutes factures (CA)
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="bilan_paiements_{du}_{au}.csv"'
    w = csv.writer(resp, delimiter=';')
    w.writerow(['Date','Réf','Payeur','Montant','Devise','Expéditeur','Destinataire','Agence'])
    for f in fact.order_by("date_colis","ref_colis"):
        w.writerow([f.date_colis, f.ref_colis, f.get_qui_paye_display(), f.montant, f.devise, f.exp_nom, f.des_nom, f.des_agence])
    return resp

def export_ca_csv(request):
    du, au = _range_du_au(request)
    agence = request.GET.get("agence") or ""
    k = _compute_caisse_and_ca(request, du, au, agence)
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="bilan_ca_{du}_{au}.csv"'
    w = csv.writer(resp, delimiter=';')
    w.writerow(['CA Expéditeur','CA Destinataire','CA Autre','Total CA'])
    w.writerow([k["ca_exp"], k["ca_des"], k["ca_aut"], k["total_ca"]])
    return resp

def print_paiements(request):
    du, au = _range_du_au(request); agence = request.GET.get("agence") or ""
    d = _compute_caisse_and_ca(request, du, au, agence)
    return render(request, "gestion/print_paiements.html", {"du":du, "au":au, "agence":agence, "fact":d["fact"], "today": now()})

def print_ca(request):
    du, au = _range_du_au(request); agence = request.GET.get("agence") or ""
    d = _compute_caisse_and_ca(request, du, au, agence)
    return render(request, "gestion/print_ca.html", {"du":du, "au":au, "agence":agence, "k":d, "today": now()})

def _staff_required(user):
    return user.is_active and (user.is_staff or user.is_superuser)


def get_period_dates(request):
    today = timezone.localdate()
    period = request.GET.get("periode", "jour")

    date_from = None
    date_to = None

    if period == "jour":
        date_from = today
        date_to = today

    elif period == "semaine":
        date_from = today - timedelta(days=today.weekday())
        date_to = date_from + timedelta(days=6)

    elif period == "mois":
        date_from = today.replace(day=1)
        if date_from.month == 12:
            next_month = date_from.replace(year=date_from.year + 1, month=1, day=1)
        else:
            next_month = date_from.replace(month=date_from.month + 1, day=1)
        date_to = next_month - timedelta(days=1)

    elif period == "libre":
        du = request.GET.get("bilan_du")
        au = request.GET.get("bilan_au")

        if du:
            try:
                date_from = datetime.strptime(du, "%Y-%m-%d").date()
            except ValueError:
                date_from = None

        if au:
            try:
                date_to = datetime.strptime(au, "%Y-%m-%d").date()
            except ValueError:
                date_to = None

    return period, date_from, date_to


def apply_date_filter(queryset, field_name, date_from, date_to):
    filters = {}

    if date_from:
        filters[f"{field_name}__gte"] = date_from

    if date_to:
        filters[f"{field_name}__lte"] = date_to

    return queryset.filter(**filters)


def get_fret_bilan(queryset):
    return queryset.aggregate(
        nb_operations=Count("id"),
        total_prix_fret=Coalesce(Sum("prix_fret_euros"), Decimal("0.00")),
        total_restant=Coalesce(Sum("restant_euros"), Decimal("0.00")),
        total_poids=Coalesce(Sum("poids_kg"), Decimal("0.00")),
        total_nb_colis=Coalesce(Sum("nb_colis_total"), 0),
    )


def get_transfert_bilan(queryset):
    return queryset.aggregate(
        nb_operations=Count("id"),
        total_envoye=Coalesce(Sum("montant_envoye"), Decimal("0.00")),
        total_frais=Coalesce(Sum("frais_transfert"), Decimal("0.00")),
        total_a_payer=Coalesce(Sum("montant_total_payer"), Decimal("0.00")),
        total_a_recevoir=Coalesce(Sum("montant_reception"), Decimal("0.00")),
    )

@ login_required(login_url='/accounts/login/')
@ user_passes_test(_staff_required)
def dashboard(request):
    colis_form = ColisRecuForm()
    envoye_form = ColisEnvoyeForm()
    facture_form = FactureForm()
    devis_form = DevisForm()
    ballon_form = BallonForm()
    ballon_item_form = BallonItemForm()
    transfert_form = TransfertArgentForm()

    current_tab = "recu"

    sms_initial = {}
    sms_numeros = request.GET.get("sms_numeros", "").strip()
    sms_message = request.GET.get("sms_message", "").strip()

    if sms_numeros:
        sms_initial["numeros"] = sms_numeros
    if sms_message:
        sms_initial["message"] = sms_message

    sms_form = EnvoyerSMSForm(initial=sms_initial)

    if request.method == "POST":
        form_type = request.POST.get("_form", "").strip()

        if form_type == "colis_recu":
            current_tab = "recu"
            colis_form = ColisRecuForm(request.POST)
            if colis_form.is_valid():
                obj = colis_form.save()
                messages.success(request, f"Fret enregistré avec la référence {obj.reference}.")
                return redirect("/app/#recu")
            else:
                messages.error(request, "Le formulaire Fret contient des erreurs.")

        elif form_type == "colis_envoye":
            current_tab = "envoye"
            envoye_form = ColisEnvoyeForm(request.POST)
            if envoye_form.is_valid():
                envoye_form.save()
                messages.success(request, "Colis envoyé enregistré.")
                return redirect("/app/#envoye")
            else:
                messages.error(request, "Le formulaire Colis contient des erreurs.")

        elif form_type == "facture":
            current_tab = "facture"
            facture_form = FactureForm(request.POST)
            if facture_form.is_valid():
                facture = facture_form.save(commit=False)

                if request.user.is_authenticated:
                    facture.cree_par = request.user
                    facture.modifie_par = request.user

                action = request.POST.get("action", "save")
                if action == "save_validate" and facture.statut == "BROUILLON":
                    facture.statut = "VALIDE"

                facture.save()
                messages.success(request, f"Facture enregistrée : {facture.numero}")
                return redirect("/app/#facture")
            else:
                print("ERREURS FACTURE =", facture_form.errors.as_json())
                messages.error(request, "Le formulaire Facture contient des erreurs.")

        elif form_type == "devis":
            current_tab = "devis"
            devis_form = DevisForm(request.POST)
            if devis_form.is_valid():
                devis = devis_form.save()
                messages.success(request, f"Devis enregistré : {getattr(devis, 'numero', '')}")
                return redirect("/app/#devis")
            else:
                print("ERREURS DEVIS =", devis_form.errors.as_json())
                messages.error(request, "Le formulaire Devis contient des erreurs.")

        elif form_type == "sms":
            current_tab = "sms"
            sms_form = EnvoyerSMSForm(request.POST)
            if sms_form.is_valid():
                sms_form.save()
                messages.success(request, "Message SMS enregistré.")
                return redirect("/app/#sms")
            else:
                print("ERREURS SMS =", sms_form.errors.as_json())
                messages.error(request, "Le formulaire SMS contient des erreurs.")

        elif form_type == "sms_delete":
            current_tab = "sms"
            sms_id = request.POST.get("sms_id")
            SMSMessage.objects.filter(pk=sms_id).delete()
            messages.success(request, "Message SMS supprimé.")
            return redirect("/app/#sms")

        elif form_type == "transfert_argent":
            current_tab = "envoye"
            transfert_form = TransfertArgentForm(request.POST)
            if transfert_form.is_valid():
                obj = transfert_form.save()
                messages.success(request, f"Transfert enregistré : {obj.reference}")
                return redirect("/app/#envoye")
            else:
                print("ERREURS TRANSFERT =", transfert_form.errors.as_json())
                messages.error(request, "Le formulaire Colis contient des erreurs.")

    colis_list = ColisRecu.objects.all().order_by("-date_enregistrement", "-id")
    envoye_list = ColisEnvoye.objects.all().order_by("-date_envoi", "-id")
    facture_list = Facture.objects.all().order_by("-date_facture", "-created_at")
    sms_list = SMSMessage.objects.all().order_by("-created_at")
    transfert_list = TransfertArgent.objects.all().order_by("-date_transfert", "-id")

    # Bilans
    period, date_from, date_to = get_period_dates(request)

    colis_bilan_qs = ColisRecu.objects.all()
    colis_bilan_qs = apply_date_filter(
        colis_bilan_qs,
        "date_enregistrement",
        date_from,
        date_to,
    )

    transfert_bilan_qs = TransfertArgent.objects.all()
    transfert_bilan_qs = apply_date_filter(
        transfert_bilan_qs,
        "date_transfert",
        date_from,
        date_to,
    )

    # BILAN FRET
    fret_period, fret_du, fret_au = get_named_period_dates(request, "fret")
    fret_bilan_qs = ColisRecu.objects.all()
    fret_bilan_qs = apply_date_filter(fret_bilan_qs, "date_enregistrement", fret_du, fret_au)
    fret_bilan = get_fret_bilan(fret_bilan_qs)

    # BILAN TRANSFERT
    transfert_period, transfert_du, transfert_au = get_named_period_dates(request, "transfert")
    transfert_bilan_qs = TransfertArgent.objects.all()
    transfert_bilan_qs = apply_date_filter(transfert_bilan_qs, "date_transfert", transfert_du, transfert_au)
    transfert_bilan = get_transfert_bilan(transfert_bilan_qs)
    transfert_sous_totaux = get_transfert_sous_totaux(transfert_bilan_qs)

    context = {
        "colis_form": colis_form,
        "envoye_form": envoye_form,
        "facture_form": facture_form,
        "devis_form": devis_form,
        "sms_form": sms_form,
        "ballon_form": ballon_form,
        "ballon_item_form": ballon_item_form,
        "colis_list": colis_list,
        "envoye_list": envoye_list,
        "facture_list": facture_list,
        "sms_list": sms_list,
        "search_results": None,
        "bilan": {
            "filters": {},
            "reset": {},
            "ops": [],
            "payes_par_exp": [],
            "payes_par_des": [],
            "since_reset": "",
        },
        "bilan_form": BilanFilterForm(),
        "ballons": [],
        "selected_ballon": None,
        "transfert_form": transfert_form,
        "transfert_list": transfert_list,
        "current_tab": current_tab,

        "fret_period": fret_period,
        "fret_du": fret_du,
        "fret_au": fret_au,
        "fret_bilan": fret_bilan,
        "fret_bilan_list": fret_bilan_qs.order_by("-date_enregistrement", "-id")[:100],

        "transfert_period": transfert_period,
        "transfert_du": transfert_du,
        "transfert_au": transfert_au,
        "transfert_bilan": transfert_bilan,
        "transfert_bilan_list": transfert_bilan_qs.order_by("-date_transfert", "-created_at")[:100],
        "transfert_sous_totaux": transfert_sous_totaux,
    }

    return render(request, "gestion/dashboard.html", context)
    
def _filtered_colis_queryset(request):
    """
    Construit une liste Python (triée) de colis reçus + envoyés
    selon les filtres GET. Chaque item est un dict homogène.
    """
    q_ref  = request.GET.get('ref', '').strip()
    q_tel  = request.GET.get('tel', '').strip()
    q_nom  = request.GET.get('nom', '').strip()
    q_type = request.GET.get('type', 'ALL').upper()   # ALL|RECU|ENVOYE
    q_stat = request.GET.get('statut', '').strip()    # OK|ATT|LIVR (optionnel)
    q_du   = request.GET.get('du', '').strip()
    q_au   = request.GET.get('au', '').strip()

    # Colis reçus
    recu_qs = ColisRecu.objects.all()
    if q_ref: recu_qs = recu_qs.filter(reference__icontains=q_ref)
    if q_tel: recu_qs = recu_qs.filter(expediteur_tel__icontains=q_tel) | recu_qs.filter(destinataire_tel__icontains=q_tel)
    if q_nom: recu_qs = recu_qs.filter(expediteur_nom__icontains=q_nom) | recu_qs.filter(destinataire_nom__icontains=q_nom)
    if q_stat: recu_qs = recu_qs.filter(statut=q_stat)
    if q_du: recu_qs = recu_qs.filter(date_enregistrement__gte=q_du)
    if q_au: recu_qs = recu_qs.filter(date_enregistrement__lte=q_au)

    recu_vals = recu_qs.annotate(
    kind=Value('RECU', output_field=CharField()),
    date=F('date_enregistrement'),

    # ✅ champs homogènes pour la table
    prix_fret=F('prix_fret_euros'),
    restant=F('restant_euros'),

    tel=F('expediteur_tel'),
    tel_dest=F('destinataire_tel'),
    nom=F('expediteur_nom'),
    nom_dest=F('destinataire_nom'),
    ).values(
        'id','kind','statut','reference',
        'nom','tel','date',
        'prix_fret','restant',
        'nbs','description',
        'nom_dest','tel_dest',
        'poids_kg'
    )
    # Colis envoyés
    env_qs = ColisEnvoye.objects.all()
    if q_ref: env_qs = env_qs.filter(reference__icontains=q_ref)
    if q_tel: env_qs = env_qs.filter(expediteur_tel__icontains=q_tel) | env_qs.filter(destinataire_tel__icontains=q_tel)
    if q_nom: env_qs = env_qs.filter(expediteur_nom__icontains=q_nom) | env_qs.filter(destinataire_nom__icontains=q_nom)
    if q_stat: env_qs = env_qs.filter(statut=q_stat)
    if q_du: env_qs = env_qs.filter(date_envoi__gte=q_du)
    if q_au: env_qs = env_qs.filter(date_envoi__lte=q_au)

    env_vals = env_qs.annotate(
        kind=Value('ENVOYE', output_field=CharField()),
        date=F('date_envoi'),

        prix_fret=F('prix_euros'),
        restant=Value(None, output_field=CharField()),  # ou DecimalField si tu veux

        tel=F('expediteur_tel'),
        tel_dest=F('destinataire_tel'),
        nom=F('expediteur_nom'),
        nom_dest=F('destinataire_nom'),
        nbs=Value('', output_field=CharField()),
    ).values(
        'id','kind','statut','reference',
        'nom','tel','date',
        'prix_fret','restant',
        'nbs','description',
        'nom_dest','tel_dest',
        'poids_kg'
    )

    if q_type == 'RECU':
        merged = list(recu_vals)
    elif q_type == 'ENVOYE':
        merged = list(env_vals)
    else:
        merged = list(chain(recu_vals, env_vals))

    # tri desc par date (None en bas)
    merged.sort(key=lambda x: (x['date'] is None, x['date']), reverse=True)
    return merged

def export_colis(request):
    rows = _filtered_colis_queryset(request)

    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="colis_export.csv"'
    writer = csv.writer(resp, delimiter=';')
    writer.writerow(['Type','Statut','Référence','Expéditeur','Tél exp','Date','Prix','NBs','Description','Destinataire','Tél dest','Poids'])
    for r in rows:
        writer.writerow([r['kind'], r['statut'], r['reference'], r['nom'], r['tel'], r['date'], r['prix'], r['nbs'], r['description'], r['nom_dest'], r['tel_dest'], r['poids_kg']])
    return resp

def _get_colis(kind, pk):
    kind = kind.upper()
    if kind == "RECU":
        return "RECU", get_object_or_404(ColisRecu, pk=pk)
    elif kind == "ENVOYE":
        return "ENVOYE", get_object_or_404(ColisEnvoye, pk=pk)
    raise HttpResponse(status=404)

def colis_view(request, kind, pk):
    kind, obj = _get_colis(kind, pk)
    return render(request, "gestion/colis_view.html", {"kind": kind, "obj": obj})

def colis_edit(request, kind, pk):
    kind, obj = _get_colis(kind, pk)
    Form = ColisRecuForm if kind == "RECU" else ColisEnvoyeForm

    if request.method == "POST":
        form = Form(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Colis mis à jour.")
            # retour vers l’onglet de départ
            return redirect("/app/#recherche")
    else:
        form = Form(instance=obj)

    return render(request, "gestion/colis_edit.html", {"kind": kind, "obj": obj, "form": form})

def colis_print(request, kind, pk):
    kind, obj = _get_colis(kind, pk)
    # page HTML imprimable (Ctrl+P)
    return render(request, "gestion/colis_print.html", {"kind": kind, "obj": obj, "today": now()})

def facture_view(request, pk):
    fac = get_object_or_404(Facture, pk=pk)
    return render(request, "gestion/facture_view.html", {"obj": fac})

def facture_print(request, pk):
    fac = get_object_or_404(Facture, pk=pk)
    return render(request, "gestion/facture_print.html", {"obj": fac, "today": now()})

def devis_convert_to_facture(request, pk):
    dev = get_object_or_404(Facture, pk=pk, type_piece="DEVIS")
    dev.type_piece = "FACTURE"
    dev.save(update_fields=["type_piece"])
    messages.success(request, f"Devis {dev.ref_colis} converti en FACTURE.")
    return redirect("/app/#facture")

@login_required
def sms_list(request):
    sms_list = SMSMessage.objects.all().order_by("-created_at")

    # Ajouter un message
    if request.method == "POST":
        form = SMSMessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("sms")
    else:
        form = SMSMessageForm()

    return render(request, "gestion/sms_list.html", {
        "sms_list": sms_list,
        "form": form,
    })


@login_required
def sms_delete(request, id):
    SMSMessage.objects.filter(id=id).delete()
    return redirect("sms")

def staff_required(u):
    return u.is_authenticated and (u.is_staff or u.is_superuser)

@login_required
def fret_detail(request, pk):
    obj = get_object_or_404(ColisRecu, pk=pk)
    return render(request, "gestion/fret_detail.html", {"obj": obj})

@login_required
def fret_edit(request, pk):
    obj = get_object_or_404(ColisRecu, pk=pk)
    ancien_statut = obj.statut

    if request.method == "POST":
        form = ColisRecuForm(request.POST, instance=obj)
        if form.is_valid():
            fret = form.save()

            if fret.statut != ancien_statut:
                try:
                    result = send_fret_status_sms_if_enabled(fret)

                    if result.get("sent"):
                        SMSLog.objects.create(
                            numero=fret.destinataire_tel or "",
                            client_nom=fret.destinataire_nom,
                            message=result["message"],
                            statut="success",
                            provider="brevo",
                            provider_message_id=str(result["response"].get("messageId", "")),
                            cree_par=request.user if request.user.is_authenticated else None,
                        )
                        messages.success(
                            request,
                            f"Le fret {fret.reference} a bien été mis à jour. SMS automatique envoyé."
                        )
                    else:
                        messages.success(
                            request,
                            f"Le fret {fret.reference} a bien été mis à jour."
                        )
                        messages.info(
                            request,
                            f"SMS non envoyé : {result.get('reason', 'désactivé')}."
                        )

                except SMSServiceError as exc:
                    SMSLog.objects.create(
                        numero=fret.destinataire_tel or "",
                        client_nom=fret.destinataire_nom,
                        message=build_fret_status_sms(fret),
                        statut="error",
                        provider="brevo",
                        erreur=str(exc),
                        cree_par=request.user if request.user.is_authenticated else None,
                    )
                    messages.success(
                        request,
                        f"Le fret {fret.reference} a bien été mis à jour."
                    )
                    messages.error(
                        request,
                        f"Erreur lors de l'envoi du SMS : {exc}"
                    )
            else:
                messages.success(request, f"Le fret {fret.reference} a bien été mis à jour.")

            return redirect("dashboard")
        else:
            messages.error(request, "Le formulaire contient des erreurs. Merci de vérifier les champs.")
    else:
        form = ColisRecuForm(instance=obj)

    return render(request, "gestion/fret_edit.html", {
        "form": form,
        "obj": obj,
        "sms_auto_send_enabled": settings.SMS_AUTO_SEND_ENABLED,
    })


@login_required
def fret_delete(request, pk):
    obj = get_object_or_404(ColisRecu, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Fret supprimé.")
        return redirect("/app/#recu")
    return render(request, "gestion/fret_delete.html", {"obj": obj})

def _qr_to_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=2,
        box_size=6,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def fret_print(request, pk):
    obj = get_object_or_404(ColisRecu, pk=pk)

    total = obj.nb_colis_total if obj.nb_colis_total and obj.nb_colis_total > 0 else 1

    labels = []
    for i in range(1, total + 1):
        qr_payload = request.build_absolute_uri(
            f"/app/tracking/{obj.reference}/?piece={i}-{total}"
        )
        labels.append({
            "index": i,
            "total": total,
            "qr_b64": _qr_to_base64(qr_payload),
        })

    return render(
        request,
        "gestion/fret_print_label_adl.html",
        {
            "obj": obj,
            "labels": labels,
        },
    )

def transfert_detail(request, pk):
    obj = get_object_or_404(TransfertArgent, pk=pk)
    return render(request, "gestion/transfert_detail.html", {"obj": obj})

def transfert_edit(request, pk):
    obj = get_object_or_404(TransfertArgent, pk=pk)
    if request.method == "POST":
        form = TransfertArgentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Transfert modifié.")
            return redirect("/app/#envoye")
    else:
        form = TransfertArgentForm(instance=obj)
    return render(request, "gestion/transfert_edit.html", {"form": form, "obj": obj})

def transfert_delete(request, pk):
    obj = get_object_or_404(TransfertArgent, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Transfert supprimé.")
        return redirect("/app/#envoye")
    return render(request, "gestion/transfert_delete.html", {"obj": obj})

def transfert_print(request, pk):
    obj = get_object_or_404(TransfertArgent, pk=pk)

    qr_payload = request.build_absolute_uri(f"/app/tracking-transfert/{obj.reference}/")
    qr_b64 = _qr_to_base64(qr_payload)

    return render(
        request,
        "gestion/transfert_print_label_adl.html",
        {
            "obj": obj,
            "qr_b64": qr_b64,
        },
    )
    
def tracking_colis(request, reference):
    obj = get_object_or_404(ColisRecu, reference=reference)

    total = obj.nb_colis_total if obj.nb_colis_total and obj.nb_colis_total > 0 else 1
    piece = request.GET.get("piece", "")

    # Progression visuelle selon statut
    if obj.statut == "ATT":
        progress_percent = 35
        status_message = "Votre colis a bien été enregistré et est en attente de traitement."
        status_class = "att"
    elif obj.statut == "OK":
        progress_percent = 70
        status_message = "Votre colis est pris en charge et en cours d’acheminement."
        status_class = "ok"
    elif obj.statut == "LIVR":
        progress_percent = 100
        status_message = "Votre colis a été livré ou marqué comme disponible."
        status_class = "livr"
    else:
        progress_percent = 20
        status_message = "Le statut du colis est en cours de mise à jour."
        status_class = "att"

    context = {
        "obj": obj,
        "total": total,
        "piece": piece,
        "progress_percent": progress_percent,
        "status_message": status_message,
        "status_class": status_class,
    }
    return render(request, "gestion/tracking_colis.html", context)
    
 
def tracking_transfert(request, reference):
    obj = get_object_or_404(TransfertArgent, reference=reference)

    if obj.statut == "ATT":
        progress_percent = 35
        status_message = "Votre transfert a bien été enregistré et est en attente de traitement."
        status_class = "att"
    elif obj.statut == "OK":
        progress_percent = 70
        status_message = "Votre transfert est validé et en cours de traitement."
        status_class = "ok"
    elif obj.statut == "PAYE":
        progress_percent = 100
        status_message = "Le transfert a été retiré par le bénéficiaire."
        status_class = "paye"
    else:
        progress_percent = 20
        status_message = "Le statut du transfert est en cours de mise à jour."
        status_class = "att"

    return render(request, "gestion/tracking_transfert.html", {
        "obj": obj,
        "progress_percent": progress_percent,
        "status_message": status_message,
        "status_class": status_class,
    })

def bilan_pdf(request):
    from weasyprint import HTML

    bilan_context = build_bilan_context(request)

    context = {
        **bilan_context,
        "print_date": timezone.localtime(),
        "logo_url": request.build_absolute_uri(settings.STATIC_URL + "gestion/img/logo-adl.png"),
        "signature_nom": "AD Logistics & Services",
        "signature_role": "Direction",
    }

    html_string = render_to_string("gestion/bilan_pdf.html", context, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="bilan_ad_logistics.pdf"'
    return response
    

def bilan_fret_pdf(request):
    from weasyprint import HTML

    fret_period, fret_du, fret_au = get_named_period_dates(request, "fret")
    fret_qs = ColisRecu.objects.all()
    fret_qs = apply_date_filter(fret_qs, "date_enregistrement", fret_du, fret_au)
    fret_bilan = get_fret_bilan(fret_qs)

    context = {
        "fret_period": fret_period,
        "fret_du": fret_du,
        "fret_au": fret_au,
        "fret_bilan": fret_bilan,
        "fret_bilan_list": fret_qs.order_by("-date_enregistrement", "-id")[:100],
        "print_date": timezone.localtime(),
        "logo_url": request.build_absolute_uri(settings.STATIC_URL + "gestion/img/logo-adl.png"),
        "signature_nom": "AD Logistics & Services",
        "signature_role": "Direction",
    }

    html_string = render_to_string("gestion/bilan_fret_pdf.html", context, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="bilan_fret_ad_logistics.pdf"'
    return response


def bilan_transfert_pdf(request):
    from weasyprint import HTML

    transfert_period, transfert_du, transfert_au = get_named_period_dates(request, "transfert")
    transfert_qs = TransfertArgent.objects.all()
    transfert_qs = apply_date_filter(transfert_qs, "date_transfert", transfert_du, transfert_au)

    transfert_bilan = get_transfert_bilan(transfert_qs)
    transfert_sous_totaux = get_transfert_sous_totaux(transfert_qs)

    context = {
        "transfert_period": transfert_period,
        "transfert_du": transfert_du,
        "transfert_au": transfert_au,
        "transfert_bilan": transfert_bilan,
        "transfert_bilan_list": transfert_qs.order_by("-date_transfert", "-created_at")[:100],
        "transfert_sous_totaux": transfert_sous_totaux,
        "print_date": timezone.localtime(),
        "logo_url": request.build_absolute_uri(settings.STATIC_URL + "gestion/img/logo-adl.png"),
        "signature_nom": "AD Logistics & Services",
        "signature_role": "Direction",
    }

    html_string = render_to_string("gestion/bilan_transfert_pdf.html", context, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="bilan_transfert_ad_logistics.pdf"'
    return response
    

@login_required
def envoyer_sms(request):
    form = EnvoyerSMSForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        numeros = form.cleaned_data["numeros"]
        message_sms = form.cleaned_data["message"]

        succes = 0
        echecs = []

        for numero in numeros:
            try:
                send_sms_brevo(numero, message_sms)
                succes += 1
            except SMSServiceError as exc:
                echecs.append(f"{numero} : {exc}")

        if succes:
            messages.success(request, f"{succes} SMS envoyé(s) avec succès.")

        if echecs:
            for err in echecs[:10]:
                messages.error(request, err)

            if len(echecs) > 10:
                messages.error(request, f"{len(echecs) - 10} autre(s) erreur(s) non affichée(s).")

        if succes and not echecs:
            return redirect("envoyer_sms")

    return render(request, "gestion/envoyer_sms.html", {
        "form": form,
        "titre_page": "Envoyer des SMS",
    })
    
    
def sms_detail(request, pk):
    sms = get_object_or_404(SMSLog, pk=pk)
    return render(request, "gestion/sms_detail.html", {"sms": sms})


def sms_renvoyer(request, pk):
    sms = get_object_or_404(SMSLog, pk=pk)

    try:
        response = send_sms_brevo(sms.numero, sms.message)

        SMSLog.objects.create(
            numero=sms.numero,
            client_nom=getattr(sms, "client_nom", ""),
            message=sms.message,
            statut="success",
            provider="brevo",
            provider_message_id=str(response.get("messageId", "")),
            cree_par=request.user if request.user.is_authenticated else None,
        )
        messages.success(request, f"SMS renvoyé à {sms.numero} avec succès.")

    except SMSServiceError as exc:
        SMSLog.objects.create(
            numero=sms.numero,
            client_nom=getattr(sms, "client_nom", ""),
            message=sms.message,
            statut="error",
            provider="brevo",
            erreur=str(exc),
            cree_par=request.user if request.user.is_authenticated else None,
        )
        messages.error(request, f"Échec du renvoi du SMS à {sms.numero} : {exc}")

    return redirect("/app/#sms")


def sms_modifier(request, pk):
    sms = get_object_or_404(SMSLog, pk=pk)

    if request.method == "POST":
        form = SMSLogEditForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data["numero"]
            message_sms = form.cleaned_data["message"]

            try:
                response = send_sms_brevo(numero, message_sms)

                SMSLog.objects.create(
                    numero=numero,
                    client_nom=getattr(sms, "client_nom", ""),
                    message=message_sms,
                    statut="success",
                    provider="brevo",
                    provider_message_id=str(response.get("messageId", "")),
                    cree_par=request.user if request.user.is_authenticated else None,
                )
                messages.success(request, "SMS modifié et renvoyé avec succès.")
                return redirect("/app/#sms")

            except SMSServiceError as exc:
                SMSLog.objects.create(
                    numero=numero,
                    client_nom=getattr(sms, "client_nom", ""),
                    message=message_sms,
                    statut="error",
                    provider="brevo",
                    erreur=str(exc),
                    cree_par=request.user if request.user.is_authenticated else None,
                )
                messages.error(request, f"Erreur lors du renvoi : {exc}")
    else:
        form = SMSLogEditForm(initial={
            "numero": sms.numero,
            "message": sms.message,
        })

    return render(request, "gestion/sms_modifier.html", {
        "sms": sms,
        "form": form,
    })


def sms_supprimer(request, pk):
    sms = get_object_or_404(SMSLog, pk=pk)

    if request.method == "POST":
        sms.delete()
        messages.success(request, "Historique SMS supprimé avec succès.")
        return redirect("/app/#sms")

    return render(request, "gestion/sms_supprimer.html", {"sms": sms})


@login_required
def facture_list(request):
    qs = Facture.objects.all().order_by("-date_facture", "-created_at")

    q = request.GET.get("q", "").strip()
    statut = request.GET.get("statut", "").strip()
    type_piece = request.GET.get("type_piece", "").strip()

    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(ref_colis__icontains=q) |
            Q(exp_nom__icontains=q) |
            Q(exp_prenom__icontains=q) |
            Q(des_nom__icontains=q) |
            Q(des_prenom__icontains=q) |
            Q(exp_tel__icontains=q) |
            Q(des_tel__icontains=q)
        )

    if statut:
        qs = qs.filter(statut=statut)

    if type_piece:
        qs = qs.filter(type_piece=type_piece)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "statut": statut,
        "type_piece": type_piece,
        "statut_choices": Facture.STATUT_CHOICES,
        "type_choices": Facture.TYPE_CHOICES,
    }
    return render(request, "gestion/factures/facture_list.html", context)


@login_required
def facture_create(request):
    if request.method == "POST":
        form = FactureForm(request.POST)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.cree_par = request.user
            facture.modifie_par = request.user

            action = request.POST.get("action", "save")
            if action == "save_validate" and facture.statut == "BROUILLON":
                facture.statut = "VALIDE"

            facture.save()

            messages.success(request, f"{facture.type_piece} {facture.numero} créée avec succès.")
            return redirect("facture_detail", pk=facture.pk)
        else:
            messages.error(request, "Le formulaire contient des erreurs.")
    else:
        form = FactureForm()

    return render(request, "gestion/factures/facture_form.html", {
        "form": form,
        "page_title": "Nouvelle facture",
        "submit_label": "Enregistrer",
        "facture": None,
    })


@login_required
def facture_update(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    if request.method == "POST":
        form = FactureForm(request.POST, instance=facture)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.modifie_par = request.user

            action = request.POST.get("action", "save")
            if action == "save_validate" and facture.statut == "BROUILLON":
                facture.statut = "VALIDE"

            facture.save()

            messages.success(request, f"{facture.type_piece} {facture.numero} modifiée avec succès.")
            return redirect("facture_detail", pk=facture.pk)
        else:
            messages.error(request, "Le formulaire contient des erreurs.")
    else:
        form = FactureForm(instance=facture)

    return render(request, "gestion/factures/facture_form.html", {
        "form": form,
        "page_title": f"Modifier {facture.type_piece}",
        "submit_label": "Mettre à jour",
        "facture": facture,
    })


@login_required
def facture_detail(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    paiements = facture.paiements.all() if hasattr(facture, "paiements") else []
    envois_email = facture.envois_email.all() if hasattr(facture, "envois_email") else []

    return render(request, "gestion/factures/facture_detail.html", {
        "facture": facture,
        "paiements": paiements,
        "envois_email": envois_email,
    })


@login_required
def facture_change_statut(request, pk, statut):
    facture = get_object_or_404(Facture, pk=pk)
    statuts_autorises = [s[0] for s in Facture.STATUT_CHOICES]

    if statut not in statuts_autorises:
        messages.error(request, "Statut invalide.")
        return redirect("facture_detail", pk=facture.pk)

    facture.statut = statut
    facture.modifie_par = request.user
    facture.save()

    messages.success(request, f"Le statut a été mis à jour : {facture.get_statut_display()}.")
    return redirect("facture_detail", pk=facture.pk)
    
def facture_print(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    params = ParametreFacture.objects.first()

    if not facture.qr_code_image:
        ensure_facture_qrcode(request, facture, save_model=True)
        facture.refresh_from_db()

    logo_url = ""
    try:
        if params and getattr(params, "societe_logo", None):
            logo_url = request.build_absolute_uri(params.societe_logo.url)
        else:
            static_logo = Path(settings.BASE_DIR) / "staticfiles" / "core" / "img" / "logo-adl.png"
            if static_logo.exists():
                # pour l'aperçu HTML, on passe par /static/...
                logo_url = request.build_absolute_uri("/static/core/img/logo-adl.png")
    except Exception:
        logo_url = ""

    qr_code_url = ""
    if facture.qr_code_image:
        try:
            qr_code_url = request.build_absolute_uri(facture.qr_code_image.url)
        except Exception:
            qr_code_url = ""

    return render(
        request,
        "gestion/factures/facture_pdf.html",
        {
            "facture": facture,
            "params": params,
            "logo_url": logo_url,
            "qr_code_url": qr_code_url,
            "is_pdf": False,
        },
    )
    
def facture_pdf(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    pdf_bytes = render_facture_pdf_bytes(request, facture)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{facture.numero}.pdf"'
    return response


def facture_pdf_download(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    pdf_bytes = render_facture_pdf_bytes(request, facture)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{facture.numero}.pdf"'
    return response


def facture_send_email(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    destinataire = facture.client_email_facturation
    if not destinataire:
        messages.error(request, "Aucune adresse e-mail disponible pour cette facture.")
        return redirect("/app/#panel-facture")

    params = ParametreFacture.objects.first()

    sujet = "Votre facture"
    message_txt = "Veuillez trouver votre facture en pièce jointe."
    if params:
        sujet = params.modele_email_sujet.format(
            type_piece=facture.get_type_piece_display(),
            numero=facture.numero,
            entreprise=params.nom_entreprise,
        )
        message_txt = params.modele_email_message.format(
            client_nom=facture.client_nom_complet or "",
            type_piece=facture.get_type_piece_display(),
            numero=facture.numero,
            ref_colis=facture.ref_colis or "",
            total_ttc=facture.montant_ttc,
            devise=facture.devise,
            entreprise=params.nom_entreprise,
        )

    pdf_bytes = render_facture_pdf_bytes(request, facture)

    log = HistoriqueEnvoiFacture.objects.create(
        facture=facture,
        email_destinataire=destinataire,
        sujet=sujet,
        message=message_txt,
        envoye_par=request.user if request.user.is_authenticated else None,
        succes=False,
    )

    try:
        email = EmailMessage(
            subject=sujet,
            body=message_txt,
            to=[destinataire],
        )
        email.attach(
            f"{facture.numero}.pdf",
            pdf_bytes,
            "application/pdf",
        )
        email.send(fail_silently=False)

        facture.statut = "ENVOYEE" if facture.statut in ["BROUILLON", "VALIDE"] else facture.statut
        facture.date_envoi_email = timezone.now()
        facture.modifie_par = request.user if request.user.is_authenticated else facture.modifie_par
        facture.save()

        log.succes = True
        log.save(update_fields=["succes"])

        messages.success(request, f"Facture envoyée par e-mail à {destinataire}.")
    except Exception as e:
        log.erreur = str(e)
        log.save(update_fields=["erreur"])
        messages.error(request, f"Échec de l’envoi e-mail : {e}")

    return redirect("/app/#panel-facture")


def facture_email_compose(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    if request.method == "POST":
        form = FactureEmailForm(request.POST, facture=facture)
        if form.is_valid():
            email_destinataire = form.cleaned_data["email_destinataire"]
            sujet = form.cleaned_data["sujet"]
            message_txt = form.cleaned_data["message"]

            pdf_bytes = render_facture_pdf_bytes(request, facture)

            log = HistoriqueEnvoiFacture.objects.create(
                facture=facture,
                email_destinataire=email_destinataire,
                sujet=sujet,
                message=message_txt,
                envoye_par=request.user if request.user.is_authenticated else None,
                succes=False,
            )

            try:
                email = EmailMessage(
                    subject=sujet,
                    body=message_txt,
                    to=[email_destinataire],
                )
                email.attach(
                    f"{facture.numero}.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
                email.send(fail_silently=False)

                facture.statut = "ENVOYEE" if facture.statut in ["BROUILLON", "VALIDE"] else facture.statut
                facture.date_envoi_email = timezone.now()
                if request.user.is_authenticated:
                    facture.modifie_par = request.user
                facture.save()

                log.succes = True
                log.save(update_fields=["succes"])

                messages.success(request, f"Facture envoyée à {email_destinataire}.")
                return redirect("facture_detail", pk=facture.pk)

            except Exception as e:
                log.erreur = str(e)
                log.save(update_fields=["erreur"])
                messages.error(request, f"Échec de l’envoi : {e}")
    else:
        form = FactureEmailForm(facture=facture)

    return render(
        request,
        "gestion/factures/facture_email_form.html",
        {
            "facture": facture,
            "form": form,
        },
    )

def facture_email_resend(request, pk, log_id):
    facture = get_object_or_404(Facture, pk=pk)
    log = get_object_or_404(HistoriqueEnvoiFacture, pk=log_id, facture=facture)

    initial = {
        "email_destinataire": log.email_destinataire,
        "sujet": log.sujet,
        "message": log.message,
    }
    form = FactureEmailForm(initial=initial, facture=facture)

    return render(
        request,
        "gestion/factures/facture_email_form.html",
        {
            "facture": facture,
            "form": form,
            "is_resend": True,
        },
    )

def facture_archive_pdf(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    archive_facture_pdf(request, facture)
    messages.success(request, f"PDF archivé pour {facture.numero}.")
    return redirect("facture_detail", pk=facture.pk)

def facture_refresh_qrcode(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    ensure_facture_qrcode(request, facture, save_model=True)
    messages.success(request, f"QR code mis à jour pour {facture.numero}.")
    return redirect("facture_detail", pk=facture.pk)
