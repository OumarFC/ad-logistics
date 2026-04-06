from io import BytesIO

from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
import json
from pathlib import Path
import qrcode
from django.core.files.base import ContentFile
from .models import ParametreFacture
import base64
import mimetypes
from administration.utils import get_societe_context_data

def build_absolute_media_url(request, path: str) -> str:
    if not path:
        return ""
    return request.build_absolute_uri(path)
    
def render_facture_pdf_bytes(request, facture):
    societe = get_societe_context_data()
    logo_url = build_logo_data_uri(societe.get("societe_logo", ""))

    if not facture.qr_code_image:
        ensure_facture_qrcode(request, facture, save_model=True)
        facture.refresh_from_db()

    qr_code_url = ""
    if facture.qr_code_image:
        try:
            qr_code_url = file_to_data_uri(facture.qr_code_image.path)
        except Exception:
            qr_code_url = ""

    html_string = render_to_string(
        "gestion/factures/facture_pdf.html",
        {
            "facture": facture,
            "societe": societe,
            "logo_url": logo_url,
            "qr_code_url": qr_code_url,
            "is_pdf": True,
        },
        request=request,
    )

    pdf_buffer = BytesIO()
    HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/")
    ).write_pdf(pdf_buffer)

    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

def build_facture_qr_payload(request, facture):
    return request.build_absolute_uri(f"/app/factures/{facture.pk}/")

def ensure_facture_qrcode(request, facture, save_model=True):
    qr_text = build_facture_qr_payload(request, facture)

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{facture.numero or 'facture'}-qr.png"
    facture.qr_code_image.save(filename, ContentFile(buffer.read()), save=save_model)
    return facture.qr_code_image

def archive_facture_pdf(request, facture):
    pdf_bytes = render_facture_pdf_bytes(request, facture)
    filename = f"{facture.numero}.pdf"
    facture.pdf_archive.save(filename, ContentFile(pdf_bytes), save=True)
    return facture.pdf_archive


def file_to_data_uri(file_path):
    path = Path(file_path)
    if not path.exists():
        return ""

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "image/png"

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime_type};base64,{encoded}"

def get_facture_logo_data_uri():
    # 1) priorité au logo paramétré en base
    try:
        params = ParametreFacture.objects.first()
        if params and getattr(params, "societe_logo", None):
            path = Path(params.societe_logo.path)
            if path.exists():
                return file_to_data_uri(path)
    except Exception:
        pass

    # 2) fallback sur le logo statique connu
    static_logo = Path(settings.BASE_DIR) / "staticfiles" / "core" / "img" / "logo-adl.png"
    if static_logo.exists():
        return file_to_data_uri(static_logo)

    return ""

def build_logo_data_uri(logo_value):
    if not logo_value:
        return ""

    if logo_value.startswith("/static/"):
        relative = logo_value.replace("/static/", "", 1)
        static_path = Path(settings.BASE_DIR) / "staticfiles" / relative
        if static_path.exists():
            return file_to_data_uri(static_path)

    if logo_value.startswith("/media/"):
        relative = logo_value.replace("/media/", "", 1)
        media_path = Path(settings.MEDIA_ROOT) / relative
        if media_path.exists():
            return file_to_data_uri(media_path)

    return ""