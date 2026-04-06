from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test

from .models import Agence, EntrepriseCliente, Parametre, ProfilAgent, VilleLivraison, ParametreSMS, FactureClient

User = get_user_model()

def is_admin(user):
    return user.is_superuser or user.is_staff

class ParametreForm(forms.ModelForm):
    class Meta:
        model = Parametre
        fields = [
            "entreprise",
            "categorie",
            "cle",
            "libelle",
            "type_valeur",
            "valeur",
            "fichier",
            "description",
            "ordre",
            "modifiable",
            "actif",
        ]
        widgets = {
            "entreprise": forms.Select(attrs={"class": "form-select"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "cle": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "type_valeur": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "modifiable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        type_valeur = None
        if self.data.get("type_valeur"):
            type_valeur = self.data.get("type_valeur")
        elif self.instance and self.instance.pk:
            type_valeur = self.instance.type_valeur
        else:
            type_valeur = "text"

        if type_valeur == "textarea":
            self.fields["valeur"].widget = forms.Textarea(attrs={"class": "form-control", "rows": 4})
        elif type_valeur == "bool":
            self.fields["valeur"].widget = forms.Select(
                choices=[("True", "Oui"), ("False", "Non")],
                attrs={"class": "form-select"}
            )
        elif type_valeur == "number":
            self.fields["valeur"].widget = forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
        elif type_valeur == "email":
            self.fields["valeur"].widget = forms.EmailInput(attrs={"class": "form-control"})
        elif type_valeur == "phone":
            self.fields["valeur"].widget = forms.TextInput(attrs={"class": "form-control"})
        elif type_valeur == "date":
            self.fields["valeur"].widget = forms.DateInput(attrs={"class": "form-control", "type": "date"})
        elif type_valeur == "color":
            self.fields["valeur"].widget = forms.TextInput(attrs={"class": "form-control", "type": "color"})
        elif type_valeur == "url":
            self.fields["valeur"].widget = forms.URLInput(attrs={"class": "form-control"})
        else:
            self.fields["valeur"].widget = forms.TextInput(attrs={"class": "form-control"})

@user_passes_test(is_admin)
def ajouter_parametre(request):
    if request.method == "POST":
        form = ParametreForm(request.POST)
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
        form = ParametreForm()

    return render(request, "administration/parametres/form.html", {
        "form": form,
        "titre_page": "Ajouter un paramètre",
        "section": "parametres",
        "mode": "create",
    })
    
@user_passes_test(is_admin)
def modifier_parametre(request, pk):
    parametre = get_object_or_404(Parametre, pk=pk, actif=True)

    if not parametre.modifiable:
        messages.error(request, "Ce paramètre ne peut pas être modifié.")
        return redirect("admin_liste_parametres")

    if request.method == "POST":
        form = ParametreForm(request.POST, instance=parametre)
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
        form = ParametreForm(instance=parametre)

    return render(request, "administration/parametres/form.html", {
        "form": form,
        "parametre": parametre,
        "titre_page": "Modifier un paramètre",
        "section": "parametres",
        "mode": "edit",
    })
    
class AgenceForm(forms.ModelForm):
    class Meta:
        model = Agence
        fields = [
            "entreprise",
            "nom",
            "code",
            "ville",
            "adresse",
            "telephone",
            "email",
            "responsable",
            "type_agence",
            "actif",
        ]
        widgets = {
            "entreprise": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "ville": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "responsable": forms.TextInput(attrs={"class": "form-control"}),
            "type_agence": forms.Select(attrs={"class": "form-select"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EntrepriseClienteForm(forms.ModelForm):
    class Meta:
        model = EntrepriseCliente
        fields = [
            "nom",
            "code",
            "telephone",
            "email",
            "adresse",
            "ville",
            "pays",
            "logo",
            "actif",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "ville": forms.TextInput(attrs={"class": "form-control"}),
            "pays": forms.TextInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AgentCreationForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    entreprise = forms.ModelChoiceField(
        queryset=EntrepriseCliente.objects.filter(actif=True).order_by("nom"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    agence = forms.ModelChoiceField(
        queryset=Agence.objects.filter(actif=True).select_related("entreprise").order_by("entreprise__nom", "nom"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    role = forms.ChoiceField(choices=ProfilAgent.ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    actif = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    peut_gerer_agences = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_agents = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_parametres = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_sms = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_voir_factures = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_voir_rapports = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        entreprise = cleaned_data.get("entreprise")
        agence = cleaned_data.get("agence")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")

        if entreprise and agence and agence.entreprise_id != entreprise.id:
            self.add_error("agence", "Cette agence n'appartient pas à l'entreprise sélectionnée.")

        return cleaned_data


class AgentUpdateForm(forms.Form):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))

    entreprise = forms.ModelChoiceField(
        queryset=EntrepriseCliente.objects.filter(actif=True).order_by("nom"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    agence = forms.ModelChoiceField(
        queryset=Agence.objects.filter(actif=True).select_related("entreprise").order_by("entreprise__nom", "nom"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    telephone = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    role = forms.ChoiceField(choices=ProfilAgent.ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    actif = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    peut_gerer_agences = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_agents = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_parametres = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_gerer_sms = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_voir_factures = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    peut_voir_rapports = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password_confirm = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean(self):
        cleaned_data = super().clean()
        entreprise = cleaned_data.get("entreprise")
        agence = cleaned_data.get("agence")
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if entreprise and agence and agence.entreprise_id != entreprise.id:
            self.add_error("agence", "Cette agence n'appartient pas à l'entreprise sélectionnée.")

        if new_password or new_password_confirm:
            if new_password != new_password_confirm:
                self.add_error("new_password_confirm", "Les mots de passe ne correspondent pas.")

        return cleaned_data


class VilleLivraisonForm(forms.ModelForm):
    class Meta:
        model = VilleLivraison
        fields = [
            "entreprise",
            "nom",
            "pays",
            "zone",
            "frais_livraison",
            "delai_estime_jours",
            "actif",
        ]
        widgets = {
            "entreprise": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "pays": forms.TextInput(attrs={"class": "form-control"}),
            "zone": forms.TextInput(attrs={"class": "form-control"}),
            "frais_livraison": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "delai_estime_jours": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ParametreSMSForm(forms.ModelForm):
    class Meta:
        model = ParametreSMS
        fields = [
            "entreprise",
            "fournisseur",
            "api_key",
            "sender_name",
            "sms_actif",
            "modele_creation",
            "modele_arrivee",
            "modele_livraison",
            "modele_transfert",
            "notes",
        ]
        widgets = {
            "entreprise": forms.Select(attrs={"class": "form-select"}),
            "fournisseur": forms.Select(attrs={"class": "form-select"}),
            "api_key": forms.TextInput(attrs={"class": "form-control"}),
            "sender_name": forms.TextInput(attrs={"class": "form-control"}),
            "sms_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "modele_creation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "modele_arrivee": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "modele_livraison": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "modele_transfert": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        

class FactureClientForm(forms.ModelForm):
    class Meta:
        model = FactureClient
        fields = [
            "entreprise",
            "type_facture",
            "statut",
            "date_emission",
            "date_echeance",
            "periode_debut",
            "periode_fin",
            "montant_ht",
            "tva",
            "devise",
            "mode_paiement",
            "description",
            "observations",
        ]
        widgets = {
            "entreprise": forms.Select(attrs={"class": "form-select"}),
            "type_facture": forms.Select(attrs={"class": "form-select"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "date_emission": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "date_echeance": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "periode_debut": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "periode_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "montant_ht": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tva": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "devise": forms.TextInput(attrs={"class": "form-control"}),
            "mode_paiement": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }