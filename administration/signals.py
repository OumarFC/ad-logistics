from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import ProfilAgent, RapportConnexion


def get_client_ip_from_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def enregistrer_connexion(sender, request, user, **kwargs):
    profil = getattr(user, "profil_agent", None)

    RapportConnexion.objects.create(
        utilisateur=user,
        entreprise=profil.entreprise if profil else None,
        agence=profil.agence if profil else None,
        username_snapshot=user.username,
        nom_complet_snapshot=(user.get_full_name() or "").strip(),
        date_connexion=timezone.now(),
        ip_address=get_client_ip_from_request(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        statut="CONNECTE",
    )


@receiver(user_logged_out)
def enregistrer_deconnexion(sender, request, user, **kwargs):
    if not user:
        return

    rapport = RapportConnexion.objects.filter(
        utilisateur=user,
        statut="CONNECTE",
        date_deconnexion__isnull=True
    ).order_by("-date_connexion").first()

    if rapport:
        rapport.date_deconnexion = timezone.now()
        rapport.statut = "DECONNECTE"
        rapport.save(update_fields=["date_deconnexion", "statut"])