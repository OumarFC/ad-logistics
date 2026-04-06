from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import (
    AgenceForm,
    AgentCreationForm,
    AgentUpdateForm,
    EntrepriseClienteForm,
    FactureClientForm,
    ParametreForm,
    ParametreSMSForm,
    VilleLivraisonForm,
)

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

User = get_user_model()


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def enregistrer_historique(request, action, module, objet, entreprise=None, description=""):
    HistoriqueAction.objects.create(
        utilisateur=request.user if request.user.is_authenticated else None,
        entreprise=entreprise,
        action=action,
        module=module,
        objet=objet,
        description=description,
        ip_address=get_client_ip(request),
    )


@user_passes_test(is_admin)
def dashboard_admin(request):
    nb_entreprises = EntrepriseCliente.objects.count()
    nb_agences = Agence.objects.count()
    nb_parametres = Parametre.objects.count()
    nb_agents = ProfilAgent.objects.count()
    nb_villes = VilleLivraison.objects.count()

    return render(request, "administration/dashboard.html", {
        "section": "dashboard",
        "nb_entreprises": nb_entreprises,
        "nb_agences": nb_agences,
        "nb_parametres": nb_parametres,
        "nb_agents": nb_agents,
        "nb_villes": nb_villes,
    })

@user_passes_test(is_admin)
def liste_parametres(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()
    categorie = request.GET.get("categorie", "").strip()

    parametres = Parametre.objects.select_related("entreprise").filter(actif=True)

    if entreprise_id:
        if entreprise_id == "global":
            parametres = parametres.filter(entreprise__isnull=True)
        else:
            parametres = parametres.filter(entreprise_id=entreprise_id)

    if categorie:
        parametres = parametres.filter(categorie=categorie)

    if q:
        parametres = parametres.filter(
            Q(libelle__icontains=q) |
            Q(cle__icontains=q) |
            Q(valeur__icontains=q) |
            Q(description__icontains=q)
        )

    parametres = parametres.order_by("categorie", "ordre", "libelle")
    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/parametres/liste.html", {
        "parametres": parametres,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "categorie_selected": categorie,
        "categories": Parametre.CATEGORIE_CHOICES,
        "section": "parametres",
    })

@user_passes_test(is_admin)
def modifier_parametre(request, pk):
    parametre = get_object_or_404(Parametre, pk=pk)

    if not parametre.modifiable:
        messages.error(request, "Ce paramètre ne peut pas être modifié.")
        return redirect("admin_liste_parametres")

    if request.method == "POST":
        form = ParametreForm(request.POST, request.FILES, instance=parametre)

        if form.is_valid():
            parametre = form.save()

            enregistrer_historique(
                request,
                action="UPDATE",
                module="Paramètres généraux",
                objet=parametre.libelle,
                entreprise=parametre.entreprise,
                description=f"Modification du paramètre {parametre.cle}."
            )

            messages.success(request, "Le paramètre a été modifié avec succès.")
            return redirect("admin_liste_parametres")
        else:
            messages.error(request, "Le formulaire contient des erreurs. Vérifiez les champs.")
    else:
        form = ParametreForm(instance=parametre)

    return render(request, "administration/parametres/form.html", {
        "form": form,
        "parametre": parametre,
        "titre_page": "Modifier un paramètre",
        "section": "parametres",
        "mode": "edit",
    })
    
@user_passes_test(is_admin)
def ajouter_parametre(request):
    if request.method == "POST":
        form = ParametreForm(request.POST, request.FILES)
        if form.is_valid():
            parametre = form.save()

            enregistrer_historique(
                request,
                action="CREATE",
                module="Paramètres généraux",
                objet=parametre.libelle,
                entreprise=parametre.entreprise,
                description=f"Création du paramètre {parametre.cle}."
            )

            messages.success(request, "Le paramètre a été ajouté avec succès.")
            return redirect("admin_liste_parametres")
        else:
            messages.error(request, "Le formulaire contient des erreurs. Vérifiez les champs.")
    else:
        form = ParametreForm()

    return render(request, "administration/parametres/form.html", {
        "form": form,
        "titre_page": "Ajouter un paramètre",
        "section": "parametres",
        "mode": "create",
    })


@user_passes_test(is_admin)
def liste_agences(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()

    agences = Agence.objects.select_related("entreprise").all()

    if entreprise_id:
        agences = agences.filter(entreprise_id=entreprise_id)

    if q:
        agences = agences.filter(
            Q(nom__icontains=q) |
            Q(code__icontains=q) |
            Q(ville__icontains=q) |
            Q(telephone__icontains=q) |
            Q(email__icontains=q) |
            Q(responsable__icontains=q) |
            Q(entreprise__nom__icontains=q)
        )

    agences = agences.order_by("entreprise__nom", "nom")
    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/agences/liste.html", {
        "agences": agences,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "section": "agences",
    })


@user_passes_test(is_admin)
def ajouter_agence(request):
    if request.method == "POST":
        form = AgenceForm(request.POST)
        if form.is_valid():
            agence = form.save()
            enregistrer_historique(
                request,
                action="CREATE",
                module="Agences",
                objet=agence.nom,
                entreprise=agence.entreprise,
                description=f"Création de l'agence {agence.nom} ({agence.code})."
            )
            messages.success(request, "Agence ajoutée avec succès.")
            return redirect("admin_liste_agences")
    else:
        form = AgenceForm()

    return render(request, "administration/agences/form.html", {
        "form": form,
        "titre_page": "Ajouter une agence",
        "section": "agences",
    })


@user_passes_test(is_admin)
def modifier_agence(request, pk):
    agence = get_object_or_404(Agence, pk=pk)

    if request.method == "POST":
        form = AgenceForm(request.POST, instance=agence)
        if form.is_valid():
            agence = form.save()
            enregistrer_historique(
                request,
                action="UPDATE",
                module="Agences",
                objet=agence.nom,
                entreprise=agence.entreprise,
                description=f"Modification de l'agence {agence.nom} ({agence.code})."
            )
            messages.success(request, "Agence modifiée avec succès.")
            return redirect("admin_liste_agences")
    else:
        form = AgenceForm(instance=agence)

    return render(request, "administration/agences/form.html", {
        "form": form,
        "agence": agence,
        "titre_page": "Modifier une agence",
        "section": "agences",
    })


@user_passes_test(is_admin)
def liste_entreprises(request):
    q = request.GET.get("q", "").strip()
    entreprises = EntrepriseCliente.objects.all()

    if q:
        entreprises = entreprises.filter(
            Q(nom__icontains=q) |
            Q(code__icontains=q) |
            Q(telephone__icontains=q) |
            Q(email__icontains=q) |
            Q(ville__icontains=q) |
            Q(pays__icontains=q) |
            Q(adresse__icontains=q)
        )

    entreprises = entreprises.order_by("nom")

    return render(request, "administration/entreprises/liste.html", {
        "entreprises": entreprises,
        "q": q,
        "section": "entreprises",
    })


@user_passes_test(is_admin)
def ajouter_entreprise(request):
    if request.method == "POST":
        form = EntrepriseClienteForm(request.POST, request.FILES)
        if form.is_valid():
            entreprise = form.save()
            enregistrer_historique(
                request,
                action="CREATE",
                module="Entreprises clientes",
                objet=entreprise.nom,
                entreprise=entreprise,
                description=f"Création de l'entreprise cliente {entreprise.nom} ({entreprise.code})."
            )
            messages.success(request, "Entreprise cliente ajoutée avec succès.")
            return redirect("admin_liste_entreprises")
    else:
        form = EntrepriseClienteForm()

    return render(request, "administration/entreprises/form.html", {
        "form": form,
        "titre_page": "Ajouter une entreprise cliente",
        "section": "entreprises",
    })


@user_passes_test(is_admin)
def modifier_entreprise(request, pk):
    entreprise = get_object_or_404(EntrepriseCliente, pk=pk)

    if request.method == "POST":
        form = EntrepriseClienteForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            entreprise = form.save()
            enregistrer_historique(
                request,
                action="UPDATE",
                module="Entreprises clientes",
                objet=entreprise.nom,
                entreprise=entreprise,
                description=f"Modification de l'entreprise cliente {entreprise.nom} ({entreprise.code})."
            )
            messages.success(request, "Entreprise cliente modifiée avec succès.")
            return redirect("admin_liste_entreprises")
    else:
        form = EntrepriseClienteForm(instance=entreprise)

    return render(request, "administration/entreprises/form.html", {
        "form": form,
        "entreprise": entreprise,
        "titre_page": "Modifier une entreprise cliente",
        "section": "entreprises",
    })


@user_passes_test(is_admin)
def liste_agents(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()

    agents = ProfilAgent.objects.select_related("user", "entreprise", "agence").all()

    if entreprise_id:
        agents = agents.filter(entreprise_id=entreprise_id)

    if q:
        agents = agents.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(telephone__icontains=q) |
            Q(role__icontains=q) |
            Q(entreprise__nom__icontains=q) |
            Q(agence__nom__icontains=q)
        )

    agents = agents.order_by("entreprise__nom", "user__username")
    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/agents/liste.html", {
        "agents": agents,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "section": "agents",
    })


@user_passes_test(is_admin)
def ajouter_agent(request):
    if request.method == "POST":
        form = AgentCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
            )

            ProfilAgent.objects.create(
                user=user,
                entreprise=form.cleaned_data["entreprise"],
                agence=form.cleaned_data["agence"],
                telephone=form.cleaned_data["telephone"],
                role=form.cleaned_data["role"],
                actif=form.cleaned_data["actif"],
                peut_gerer_agences=form.cleaned_data["peut_gerer_agences"],
                peut_gerer_agents=form.cleaned_data["peut_gerer_agents"],
                peut_gerer_parametres=form.cleaned_data["peut_gerer_parametres"],
                peut_gerer_sms=form.cleaned_data["peut_gerer_sms"],
                peut_voir_factures=form.cleaned_data["peut_voir_factures"],
                peut_voir_rapports=form.cleaned_data["peut_voir_rapports"],
            )
            
            enregistrer_historique(
                request,
                action="CREATE",
                module="Agents",
                objet=user.username,
                entreprise=profil.entreprise,
                description=f"Création de l'agent {user.username} avec le rôle {profil.role}."
            )

            messages.success(request, "Agent ajouté avec succès.")
            return redirect("admin_liste_agents")
    else:
        form = AgentCreationForm()

    return render(request, "administration/agents/form.html", {
        "form": form,
        "titre_page": "Ajouter un agent",
        "mode": "create",
        "section": "agents",
    })


@user_passes_test(is_admin)
def modifier_agent(request, pk):
    profil = get_object_or_404(
        ProfilAgent.objects.select_related("user", "entreprise", "agence"),
        pk=pk
    )
    user = profil.user

    if request.method == "POST":
        form = AgentUpdateForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()

            new_password = form.cleaned_data.get("new_password")
            if new_password:
                user.set_password(new_password)
                user.save()

            profil.entreprise = form.cleaned_data["entreprise"]
            profil.agence = form.cleaned_data["agence"]
            profil.telephone = form.cleaned_data["telephone"]
            profil.role = form.cleaned_data["role"]
            profil.actif = form.cleaned_data["actif"]
            profil.peut_gerer_agences = form.cleaned_data["peut_gerer_agences"]
            profil.peut_gerer_agents = form.cleaned_data["peut_gerer_agents"]
            profil.peut_gerer_parametres = form.cleaned_data["peut_gerer_parametres"]
            profil.peut_gerer_sms = form.cleaned_data["peut_gerer_sms"]
            profil.peut_voir_factures = form.cleaned_data["peut_voir_factures"]
            profil.peut_voir_rapports = form.cleaned_data["peut_voir_rapports"]
            profil.save()
            
            enregistrer_historique(
                request,
                action="UPDATE",
                module="Agents",
                objet=user.username,
                entreprise=profil.entreprise,
                description=f"Modification de l'agent {user.username}."
            )

            messages.success(request, "Agent modifié avec succès.")
            return redirect("admin_liste_agents")
    else:
        form = AgentUpdateForm(initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "entreprise": profil.entreprise,
            "agence": profil.agence,
            "telephone": profil.telephone,
            "role": profil.role,
            "actif": profil.actif,
            "peut_gerer_agences": profil.peut_gerer_agences,
            "peut_gerer_agents": profil.peut_gerer_agents,
            "peut_gerer_parametres": profil.peut_gerer_parametres,
            "peut_gerer_sms": profil.peut_gerer_sms,
            "peut_voir_factures": profil.peut_voir_factures,
            "peut_voir_rapports": profil.peut_voir_rapports,
        })

    return render(request, "administration/agents/form.html", {
        "form": form,
        "profil": profil,
        "titre_page": f"Modifier l'agent {user.username}",
        "mode": "edit",
        "section": "agents",
    })


@user_passes_test(is_admin)
def liste_connexions(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()
    statut = request.GET.get("statut", "").strip()

    connexions = RapportConnexion.objects.select_related("utilisateur", "entreprise", "agence").all()

    if entreprise_id:
        connexions = connexions.filter(entreprise_id=entreprise_id)

    if statut:
        connexions = connexions.filter(statut=statut)

    if q:
        connexions = connexions.filter(
            Q(username_snapshot__icontains=q) |
            Q(nom_complet_snapshot__icontains=q) |
            Q(ip_address__icontains=q) |
            Q(user_agent__icontains=q) |
            Q(entreprise__nom__icontains=q) |
            Q(agence__nom__icontains=q)
        )

    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/connexions/liste.html", {
        "connexions": connexions,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "statut_selected": statut,
        "section": "connexions",
    })
    
    
@user_passes_test(is_admin)
def liste_villes(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()

    villes = VilleLivraison.objects.select_related("entreprise").all()

    if entreprise_id:
        villes = villes.filter(entreprise_id=entreprise_id)

    if q:
        villes = villes.filter(
            Q(nom__icontains=q) |
            Q(pays__icontains=q) |
            Q(zone__icontains=q) |
            Q(entreprise__nom__icontains=q)
        )

    villes = villes.order_by("entreprise__nom", "nom")
    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/villes/liste.html", {
        "villes": villes,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "section": "villes",
    })


@user_passes_test(is_admin)
def ajouter_ville(request):
    if request.method == "POST":
        form = VilleLivraisonForm(request.POST)
        if form.is_valid():
            ville = form.save()
            enregistrer_historique(
                request,
                action="CREATE",
                module="Villes de livraison",
                objet=ville.nom,
                entreprise=ville.entreprise,
                description=f"Création de la ville de livraison {ville.nom}."
            )
            messages.success(request, "Ville de livraison ajoutée avec succès.")
            return redirect("admin_liste_villes")
    else:
        form = VilleLivraisonForm()

    return render(request, "administration/villes/form.html", {
        "form": form,
        "titre_page": "Ajouter une ville de livraison",
        "section": "villes",
    })


@user_passes_test(is_admin)
def modifier_ville(request, pk):
    ville = get_object_or_404(VilleLivraison, pk=pk)

    if request.method == "POST":
        form = VilleLivraisonForm(request.POST, instance=ville)
        if form.is_valid():
            ville = form.save()
            enregistrer_historique(
                request,
                action="UPDATE",
                module="Villes de livraison",
                objet=ville.nom,
                entreprise=ville.entreprise,
                description=f"Modification de la ville de livraison {ville.nom}."
            )
            messages.success(request, "Ville de livraison modifiée avec succès.")
            return redirect("admin_liste_villes")
    else:
        form = VilleLivraisonForm(instance=ville)

    return render(request, "administration/villes/form.html", {
        "form": form,
        "ville": ville,
        "titre_page": "Modifier une ville de livraison",
        "section": "villes",
    })

@user_passes_test(is_admin)
def liste_sms(request):
    q = request.GET.get("q", "").strip()
    sms_list = ParametreSMS.objects.select_related("entreprise").all()

    if q:
        sms_list = sms_list.filter(
            Q(entreprise__nom__icontains=q) |
            Q(fournisseur__icontains=q) |
            Q(sender_name__icontains=q)
        )

    sms_list = sms_list.order_by("entreprise__nom")

    return render(request, "administration/sms/liste.html", {
        "sms_list": sms_list,
        "q": q,
        "section": "sms",
    })


@user_passes_test(is_admin)
def ajouter_sms(request):
    if request.method == "POST":
        form = ParametreSMSForm(request.POST)
        if form.is_valid():
            param_sms = form.save()
            enregistrer_historique(
                request,
                action="CREATE",
                module="Paramétrage SMS",
                objet=param_sms.entreprise.nom,
                entreprise=param_sms.entreprise,
                description=f"Création du paramétrage SMS pour {param_sms.entreprise.nom}."
            )
            messages.success(request, "Paramétrage SMS ajouté avec succès.")
            return redirect("admin_liste_sms")
    else:
        form = ParametreSMSForm()

    return render(request, "administration/sms/form.html", {
        "form": form,
        "titre_page": "Ajouter un paramétrage SMS",
        "section": "sms",
    })


@user_passes_test(is_admin)
def modifier_sms(request, pk):
    param_sms = get_object_or_404(ParametreSMS, pk=pk)

    if request.method == "POST":
        form = ParametreSMSForm(request.POST, instance=param_sms)
        if form.is_valid():
            param_sms = form.save()
            enregistrer_historique(
                request,
                action="UPDATE",
                module="Paramétrage SMS",
                objet=param_sms.entreprise.nom,
                entreprise=param_sms.entreprise,
                description=f"Modification du paramétrage SMS pour {param_sms.entreprise.nom}."
            )
            messages.success(request, "Paramétrage SMS modifié avec succès.")
            return redirect("admin_liste_sms")
    else:
        form = ParametreSMSForm(instance=param_sms)

    return render(request, "administration/sms/form.html", {
        "form": form,
        "param_sms": param_sms,
        "titre_page": "Modifier un paramétrage SMS",
        "section": "sms",
    })

@user_passes_test(is_admin)
def liste_historique(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()
    action = request.GET.get("action", "").strip()

    historiques = HistoriqueAction.objects.select_related("utilisateur", "entreprise").all()

    if entreprise_id:
        historiques = historiques.filter(entreprise_id=entreprise_id)

    if action:
        historiques = historiques.filter(action=action)

    if q:
        historiques = historiques.filter(
            Q(objet__icontains=q) |
            Q(description__icontains=q) |
            Q(module__icontains=q) |
            Q(utilisateur__username__icontains=q)
        )

    historiques = historiques.order_by("-date_action")
    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")
    actions = HistoriqueAction.ACTION_CHOICES

    return render(request, "administration/historiques/liste.html", {
        "historiques": historiques,
        "entreprises": entreprises,
        "actions": actions,
        "q": q,
        "entreprise_id": entreprise_id,
        "action_selected": action,
        "section": "historique",
    })
 
@user_passes_test(is_admin)
def liste_factures(request):
    q = request.GET.get("q", "").strip()
    entreprise_id = request.GET.get("entreprise", "").strip()
    statut = request.GET.get("statut", "").strip()

    factures = FactureClient.objects.select_related("entreprise", "cree_par").all()

    if entreprise_id:
        factures = factures.filter(entreprise_id=entreprise_id)

    if statut:
        factures = factures.filter(statut=statut)

    if q:
        factures = factures.filter(
            Q(numero__icontains=q) |
            Q(entreprise__nom__icontains=q) |
            Q(description__icontains=q) |
            Q(observations__icontains=q)
        )

    entreprises = EntrepriseCliente.objects.filter(actif=True).order_by("nom")

    return render(request, "administration/factures/liste.html", {
        "factures": factures,
        "entreprises": entreprises,
        "q": q,
        "entreprise_id": entreprise_id,
        "statut_selected": statut,
        "section": "factures",
    })


@user_passes_test(is_admin)
def ajouter_facture(request):
    if request.method == "POST":
        form = FactureClientForm(request.POST)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.cree_par = request.user
            facture.save()

            enregistrer_historique(
                request,
                action="CREATE",
                module="Factures",
                objet=facture.numero,
                entreprise=facture.entreprise,
                description=f"Création de la facture {facture.numero} pour {facture.entreprise.nom}."
            )

            messages.success(request, "Facture ajoutée avec succès.")
            return redirect("admin_liste_factures")
    else:
        form = FactureClientForm()

    return render(request, "administration/factures/form.html", {
        "form": form,
        "titre_page": "Ajouter une facture",
        "section": "factures",
    })


@user_passes_test(is_admin)
def modifier_facture(request, pk):
    facture = get_object_or_404(FactureClient, pk=pk)

    if request.method == "POST":
        form = FactureClientForm(request.POST, instance=facture)
        if form.is_valid():
            facture = form.save()

            enregistrer_historique(
                request,
                action="UPDATE",
                module="Factures",
                objet=facture.numero,
                entreprise=facture.entreprise,
                description=f"Modification de la facture {facture.numero}."
            )

            messages.success(request, "Facture modifiée avec succès.")
            return redirect("admin_liste_factures")
    else:
        form = FactureClientForm(instance=facture)

    return render(request, "administration/factures/form.html", {
        "form": form,
        "facture": facture,
        "titre_page": f"Modifier la facture {facture.numero}",
        "section": "factures",
    })