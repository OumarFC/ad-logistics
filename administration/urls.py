from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_admin, name="dashboard_admin"),

    path("parametres/", views.liste_parametres, name="admin_liste_parametres"),
    path("parametres/ajouter/", views.ajouter_parametre, name="admin_ajouter_parametre"),
    path("parametres/<int:pk>/modifier/", views.modifier_parametre, name="admin_modifier_parametre"),

    path("agences/", views.liste_agences, name="admin_liste_agences"),
    path("agences/ajouter/", views.ajouter_agence, name="admin_ajouter_agence"),
    path("agences/<int:pk>/modifier/", views.modifier_agence, name="admin_modifier_agence"),

    path("entreprises/", views.liste_entreprises, name="admin_liste_entreprises"),
    path("entreprises/ajouter/", views.ajouter_entreprise, name="admin_ajouter_entreprise"),
    path("entreprises/<int:pk>/modifier/", views.modifier_entreprise, name="admin_modifier_entreprise"),

    path("agents/", views.liste_agents, name="admin_liste_agents"),
    path("agents/ajouter/", views.ajouter_agent, name="admin_ajouter_agent"),
    path("agents/<int:pk>/modifier/", views.modifier_agent, name="admin_modifier_agent"),
    
    path("villes/", views.liste_villes, name="admin_liste_villes"),
    path("villes/ajouter/", views.ajouter_ville, name="admin_ajouter_ville"),
    path("villes/<int:pk>/modifier/", views.modifier_ville, name="admin_modifier_ville"),
    
    path("sms/", views.liste_sms, name="admin_liste_sms"),
    path("sms/ajouter/", views.ajouter_sms, name="admin_ajouter_sms"),
    path("sms/<int:pk>/modifier/", views.modifier_sms, name="admin_modifier_sms"),
    path("historiques/", views.liste_historique, name="admin_liste_historique"),
    path("connexions/", views.liste_connexions, name="admin_liste_connexions"),
    
    path("factures/", views.liste_factures, name="admin_liste_factures"),
    path("factures/ajouter/", views.ajouter_facture, name="admin_ajouter_facture"),
    path("factures/<int:pk>/modifier/", views.modifier_facture, name="admin_modifier_facture"),
]