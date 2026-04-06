import requests
from django.conf import settings


class SMSServiceError(Exception):
    pass


def normalize_phone(phone: str) -> str:
    if phone is None:
        return ""

    if not isinstance(phone, str):
        raise SMSServiceError(f"Format téléphone invalide : {phone!r}")

    phone = phone.strip().replace(" ", "").replace("-", "").replace(".", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0") and len(phone) == 10:
        phone = "33" + phone[1:]

    return phone

def send_sms_brevo(recipient_phone: str, content: str) -> dict:
    api_key = getattr(settings, "BREVO_API_KEY", "")
    sender = getattr(settings, "BREVO_SMS_SENDER", "ADLOGISTIC")

    if not api_key:
        raise SMSServiceError("BREVO_API_KEY non configurée.")

    recipient_phone = normalize_phone(recipient_phone)

    if not recipient_phone:
        raise SMSServiceError("Numéro vide.")

    if not content or not content.strip():
        raise SMSServiceError("Message vide.")

    url = "https://api.brevo.com/v3/transactionalSMS/sms"

    payload = {
        "sender": sender,
        "recipient": recipient_phone,
        "content": content.strip(),
        "type": "transactional",
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise SMSServiceError(f"Erreur réseau : {exc}") from exc

    if response.status_code not in (200, 201, 202):
        try:
            data = response.json()
        except Exception:
            data = response.text
        raise SMSServiceError(f"Erreur Brevo ({response.status_code}) : {data}")

    try:
        return response.json()
    except Exception:
        return {"status": "accepted"}

from django.conf import settings


def build_fret_status_sms(fret) -> str:
    if fret.statut == "PEC":
        return f"AD Logistics : votre fret {fret.reference} a été pris en charge."
    if fret.statut == "ECR":
        return f"AD Logistics : votre fret {fret.reference} est en cours d'acheminement."
    if fret.statut == "ARR":
        return f"AD Logistics : votre fret {fret.reference} est arrivé. Merci de nous contacter."
    if fret.statut == "LIVR":
        return f"AD Logistics : votre fret {fret.reference} a été livré."
    return f"AD Logistics : le statut de votre fret {fret.reference} a été mis à jour."


def send_fret_status_sms_if_enabled(fret):
    message = build_fret_status_sms(fret)

    if not getattr(settings, "SMS_AUTO_SEND_ENABLED", False):
        return {
            "sent": False,
            "reason": "Envoi automatique désactivé",
            "message": message,
        }

    if not fret.destinataire_tel:
        return {
            "sent": False,
            "reason": "Aucun numéro destinataire",
            "message": message,
        }

    response = send_sms_brevo(fret.destinataire_tel, message)

    return {
        "sent": True,
        "response": response,
        "message": message,
    }