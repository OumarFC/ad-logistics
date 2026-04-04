from .models import Parametre, EntrepriseCliente


def get_param_value(entreprise=None, cle="", default=""):
    """
    Retourne la valeur d'un paramètre pour une entreprise.
    Si le paramètre n'existe pas pour l'entreprise, tente le global.
    """
    if entreprise:
        param = Parametre.objects.filter(
            entreprise=entreprise,
            cle=cle,
            actif=True,
        ).first()
        if param:
            return param.valeur

    param_global = Parametre.objects.filter(
        entreprise__isnull=True,
        cle=cle,
        actif=True,
    ).first()

    if param_global:
        return param_global.valeur

    return default


def get_param_bool(entreprise=None, cle="", default=False):
    valeur = str(get_param_value(entreprise=entreprise, cle=cle, default=str(default))).strip().lower()
    return valeur in ["true", "1", "yes", "oui"]


def get_param_number(entreprise=None, cle="", default=0):
    try:
        return float(get_param_value(entreprise=entreprise, cle=cle, default=default))
    except (TypeError, ValueError):
        return default

def get_societe_context_data():
    entreprise = EntrepriseCliente.objects.filter(actif=True).order_by("id").first()

    if not entreprise:
        return {
            "societe_courante": None,
            "societe_nom": "Plateforme logistique",
            "societe_sous_titre": "",
            "societe_logo": "",
            "societe_adresse": "",
            "societe_ville": "",
            "societe_pays": "",
            "societe_telephone_1": "",
            "societe_telephone_2": "",
            "societe_email": "",
            "societe_site_web": "",
            "societe_slogan": "",
            "societe_couleur_principale": "#0c4a78",
        }

    logo_url = ""
    p_logo = Parametre.objects.filter(
        entreprise=entreprise,
        cle="societe_logo",
        actif=True
    ).first()

    if p_logo:
        if getattr(p_logo, "fichier", None):
            try:
                logo_url = p_logo.fichier.url
            except Exception:
                logo_url = ""
        else:
            logo_url = p_logo.valeur or ""

    return {
        "societe_courante": entreprise,
        "societe_nom": get_param_value(entreprise, "societe_nom", entreprise.nom),
        "societe_sous_titre": get_param_value(entreprise, "societe_sous_titre", ""),
        "societe_logo": logo_url,
        "societe_favicon": get_param_value(entreprise, "societe_favicon", ""),
        "societe_adresse": get_param_value(entreprise, "societe_adresse", entreprise.adresse or ""),
        "societe_ville": get_param_value(entreprise, "societe_ville", entreprise.ville or ""),
        "societe_pays": get_param_value(entreprise, "societe_pays", entreprise.pays or ""),
        "societe_telephone_1": get_param_value(entreprise, "societe_telephone_1", ""),
        "societe_telephone_2": get_param_value(entreprise, "societe_telephone_2", ""),
        "societe_email": get_param_value(entreprise, "societe_email", entreprise.email or ""),
        "societe_site_web": get_param_value(entreprise, "societe_site_web", ""),
        "societe_slogan": get_param_value(entreprise, "societe_slogan", ""),
        "societe_couleur_principale": get_param_value(entreprise, "societe_couleur_principale", "#0c4a78"),
    }