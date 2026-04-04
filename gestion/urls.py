from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [

    path('', views.dashboard, name='dashboard'),
    
    path("tracking/<str:reference>/", views.tracking_colis, name="tracking_colis"),
    
    path('export-colis/', views.export_colis, name='export_colis'),  # CSV
    # Colis (recu|envoye)
    path('colis/<str:kind>/<int:pk>/view/', views.colis_view, name='colis_view'),
    path('colis/<str:kind>/<int:pk>/edit/', views.colis_edit, name='colis_edit'),
    path('colis/<str:kind>/<int:pk>/print/', views.colis_print, name='colis_print'),

    # Factures / Devis
    path('facture/<int:pk>/view/', views.facture_view, name='facture_view'),
    path('facture/<int:pk>/print/', views.facture_print, name='facture_print'),
    path('devis/<int:pk>/convert/', views.devis_convert_to_facture, name='devis_convert'),
    # exports & print (bilans)
    path('bilans/export-paiements/', views.export_paiements_csv, name='export_paiements_csv'),
    path('bilans/export-ca/',        views.export_ca_csv,        name='export_ca_csv'),
    path('bilans/print-paiements/',  views.print_paiements,      name='print_paiements'),
    path('bilans/print-ca/',         views.print_ca,             name='print_ca'),
    path('accounts/login/',  auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path("sms/", views.sms_list, name="sms"),
    path("sms/delete/<int:id>/", views.sms_delete, name="sms_delete"),
    # ✅ Actions Fret
    path("fret/<int:pk>/", views.fret_detail, name="fret_detail"),
    path("fret/<int:pk>/edit/", views.fret_edit, name="fret_edit"),
    path("fret/<int:pk>/delete/", views.fret_delete, name="fret_delete"),
    path("fret/<int:pk>/print/", views.fret_print, name="fret_print"),
    path("transfert/<int:pk>/", views.transfert_detail, name="transfert_detail"),
    path("transfert/<int:pk>/edit/", views.transfert_edit, name="transfert_edit"),
    path("transfert/<int:pk>/delete/", views.transfert_delete, name="transfert_delete"),
    path("transfert/<int:pk>/print/", views.transfert_print, name="transfert_print"),
    path("tracking-transfert/<str:reference>/", views.tracking_transfert, name="tracking_transfert"),
    path("bilan/pdf/", views.bilan_pdf, name="bilan_pdf"),
    path("bilan/fret/pdf/", views.bilan_fret_pdf, name="bilan_fret_pdf"),
    path("bilan/transfert/pdf/", views.bilan_transfert_pdf, name="bilan_transfert_pdf"),
    path("sms/envoyer/", views.envoyer_sms, name="envoyer_sms"),
    path("sms/<int:pk>/", views.sms_detail, name="sms_detail"),
    path("sms/<int:pk>/renvoyer/", views.sms_renvoyer, name="sms_renvoyer"),
    path("sms/<int:pk>/modifier/", views.sms_modifier, name="sms_modifier"),
    path("sms/<int:pk>/supprimer/", views.sms_supprimer, name="sms_supprimer"),
    
    path("factures/", views.facture_list, name="facture_list"),
    path("factures/nouvelle/", views.facture_create, name="facture_create"),
    path("factures/<int:pk>/", views.facture_detail, name="facture_detail"),
    path("factures/<int:pk>/modifier/", views.facture_update, name="facture_update"),
    path("factures/<int:pk>/statut/<str:statut>/", views.facture_change_statut, name="facture_change_statut"),
    path("factures/<int:pk>/imprimer/", views.facture_print, name="facture_print"),
    path("factures/<int:pk>/pdf/", views.facture_pdf, name="facture_pdf"),
    path("factures/<int:pk>/telecharger-pdf/", views.facture_pdf_download, name="facture_pdf_download"),
    path("factures/<int:pk>/envoyer-email/", views.facture_send_email, name="facture_send_email"),
    path("factures/<int:pk>/email/", views.facture_email_compose, name="facture_email_compose"),
    
    path("factures/<int:pk>/email/resend/<int:log_id>/", views.facture_email_resend, name="facture_email_resend"),
    path("factures/<int:pk>/archiver-pdf/", views.facture_archive_pdf, name="facture_archive_pdf"),
    path("factures/<int:pk>/refresh-qrcode/", views.facture_refresh_qrcode, name="facture_refresh_qrcode"),
]

 