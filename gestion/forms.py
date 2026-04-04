from django import forms
from .models import ColisEnvoye, ColisRecu
from .models import Facture
from .models import Ballon, BallonItem
from .models import SMSMessage
from .models import TransfertArgent
from django.utils import timezone
from .models import ParametreFacture

class ColisRecuForm(forms.ModelForm):
    class Meta:
        model = ColisRecu
        fields = [
            "statut",
            "livraison",
            "type_fret",
            "date_enregistrement",
            "agent_nom",
            "expediteur_nom",
            "expediteur_tel",
            "expediteur_adresse",
            "destinataire_nom",
            "destinataire_tel",
            "agence_destination",
            "poids_kg",
            "prix_fret_euros",
            "restant_euros",
            "nb_colis_total",
            "type_colis",
            "description",
        ]
        widgets = {
            "statut": forms.Select(attrs={"class": "form-select"}),
            "livraison": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "type_fret": forms.Select(attrs={"class": "form-select"}),
            "date_enregistrement": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "agent_nom": forms.TextInput(attrs={"class": "form-control"}),
            "expediteur_nom": forms.TextInput(attrs={"class": "form-control"}),
            "expediteur_tel": forms.TextInput(attrs={"class": "form-control"}),
            "expediteur_adresse": forms.TextInput(attrs={"class": "form-control"}),

            "destinataire_nom": forms.TextInput(attrs={"class": "form-control"}),
            "destinataire_tel": forms.TextInput(attrs={"class": "form-control"}),
            "agence_destination": forms.TextInput(attrs={"class": "form-control"}),

            "poids_kg": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "id": "id_poids_kg",
            }),
            "prix_fret_euros": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "id": "id_prix_fret_euros",
            }),
            "restant_euros": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "id": "id_restant_euros",
            }),
            "nb_colis_total": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "1",
                "min": "1",
                "id": "id_nb_colis_total",
            }),

            "type_colis": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "statut": "Statut",
            "livraison": "Livraison ?",
            "type_fret": "Type de fret",
            "date_enregistrement": "Date enr.",
            "agent_nom": "Nom de l’agent",
            "expediteur_nom": "Expéditeur",
            "expediteur_tel": "Tél. expéditeur",
            "expediteur_adresse": "Adresse expéditeur",
            "destinataire_nom": "Destinataire",
            "destinataire_tel": "Tél. destinataire",
            "agence_destination": "Agence destination",
            "poids_kg": "Poids (kg)",
            "prix_fret_euros": "Prix fret (€)",
            "restant_euros": "Restant (€)",
            "nb_colis_total": "Nombre total de colis",
            "type_colis": "Type colis",
            "description": "Description",
        }
        
        
class ColisEnvoyeForm(forms.ModelForm):
    class Meta:
        model = ColisEnvoye
        fields = "__all__"
        widgets = {
            "date_envoi": forms.DateInput(attrs={"type": "date"}),
        }



class DateInput(forms.DateInput):
    input_type = "date"


class FactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            "type_piece",
            "statut",

            "date_facture",
            "date_echeance",

            "ref_colis",
            "date_colis",
            "description",
            "produit",
            "poids_kg",
            "nb_colis",
            "des_agence",
            "livraison",

            "exp_nom",
            "exp_prenom",
            "exp_tel",
            "exp_mail",
            "exp_adresse",

            "des_nom",
            "des_prenom",
            "des_tel",
            "des_mail",
            "des_adresse",

            "qui_paye",
            "devise",

            "montant_ht",
            "taux_tva",
            "remise",
            "montant_paye",

            "note_client",
            "note_interne",
        ]
        widgets = {
            "date_facture": DateInput(attrs={"class": "form-control"}),
            "date_echeance": DateInput(attrs={"class": "form-control"}),
            "date_colis": DateInput(attrs={"class": "form-control"}),

            "type_piece": forms.Select(attrs={"class": "form-select"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "qui_paye": forms.Select(attrs={"class": "form-select"}),
            "devise": forms.TextInput(attrs={"class": "form-control"}),

            "ref_colis": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "produit": forms.TextInput(attrs={"class": "form-control"}),
            "poids_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "nb_colis": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "des_agence": forms.TextInput(attrs={"class": "form-control"}),
            "livraison": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            "exp_nom": forms.TextInput(attrs={"class": "form-control"}),
            "exp_prenom": forms.TextInput(attrs={"class": "form-control"}),
            "exp_tel": forms.TextInput(attrs={"class": "form-control"}),
            "exp_mail": forms.EmailInput(attrs={"class": "form-control"}),
            "exp_adresse": forms.TextInput(attrs={"class": "form-control"}),

            "des_nom": forms.TextInput(attrs={"class": "form-control"}),
            "des_prenom": forms.TextInput(attrs={"class": "form-control"}),
            "des_tel": forms.TextInput(attrs={"class": "form-control"}),
            "des_mail": forms.EmailInput(attrs={"class": "form-control"}),
            "des_adresse": forms.TextInput(attrs={"class": "form-control"}),

            "montant_ht": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "taux_tva": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remise": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "montant_paye": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),

            "note_client": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "note_interne": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        params = ParametreFacture.objects.first()

        if not self.instance.pk:
            self.fields["date_facture"].initial = timezone.localdate()
            self.fields["date_colis"].initial = timezone.localdate()
            self.fields["statut"].initial = "BROUILLON"

            if params:
                self.fields["devise"].initial = params.devise_defaut
                self.fields["taux_tva"].initial = params.taux_tva_defaut
                self.fields["date_echeance"].initial = (
                    timezone.localdate() + timezone.timedelta(days=params.delai_paiement_jours)
                )
            else:
                self.fields["devise"].initial = "EUR"
                self.fields["taux_tva"].initial = 0
                self.fields["date_echeance"].initial = timezone.localdate() + timezone.timedelta(days=7)

    def clean(self):
        cleaned_data = super().clean()

        montant_ht = cleaned_data.get("montant_ht") or 0
        remise = cleaned_data.get("remise") or 0
        montant_paye = cleaned_data.get("montant_paye") or 0
        date_facture = cleaned_data.get("date_facture")
        date_echeance = cleaned_data.get("date_echeance")

        if remise > montant_ht:
            self.add_error("remise", "La remise ne peut pas être supérieure au montant HT.")

        if montant_paye < 0:
            self.add_error("montant_paye", "Le montant payé ne peut pas être négatif.")

        if date_facture and date_echeance and date_echeance < date_facture:
            self.add_error("date_echeance", "La date d’échéance ne peut pas être antérieure à la date de facture.")

        return cleaned_data

class DevisForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = [
            "type_piece",
            "statut",
            "date_facture",
            "date_echeance",

            "exp_nom",
            "exp_prenom",
            "exp_tel",
            "exp_mail",
            "exp_adresse",

            "des_nom",
            "des_prenom",
            "des_tel",
            "des_mail",
            "des_agence",
            "des_adresse",
            "livraison",

            "description",
            "produit",
            "ref_colis",
            "date_colis",
            "poids_kg",
            "nb_colis",

            "qui_paye",
            "devise",
            "montant_ht",
            "taux_tva",
            "remise",
            "montant_paye",

            "note_client",
            "note_interne",
        ]
        widgets = {
            "type_piece": forms.HiddenInput(),

            "statut": forms.Select(attrs={"class": "form-select"}),
            "date_facture": DateInput(attrs={"class": "form-control"}),
            "date_echeance": DateInput(attrs={"class": "form-control"}),

            "exp_nom": forms.TextInput(attrs={"class": "form-control"}),
            "exp_prenom": forms.TextInput(attrs={"class": "form-control"}),
            "exp_tel": forms.TextInput(attrs={"class": "form-control"}),
            "exp_mail": forms.EmailInput(attrs={"class": "form-control"}),
            "exp_adresse": forms.TextInput(attrs={"class": "form-control"}),

            "des_nom": forms.TextInput(attrs={"class": "form-control"}),
            "des_prenom": forms.TextInput(attrs={"class": "form-control"}),
            "des_tel": forms.TextInput(attrs={"class": "form-control"}),
            "des_mail": forms.EmailInput(attrs={"class": "form-control"}),
            "des_agence": forms.TextInput(attrs={"class": "form-control"}),
            "des_adresse": forms.TextInput(attrs={"class": "form-control"}),
            "livraison": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            "description": forms.TextInput(attrs={"class": "form-control"}),
            "produit": forms.TextInput(attrs={"class": "form-control"}),
            "ref_colis": forms.TextInput(attrs={"class": "form-control"}),
            "date_colis": DateInput(attrs={"class": "form-control"}),

            "poids_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "nb_colis": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),

            "qui_paye": forms.Select(attrs={"class": "form-select"}),
            "devise": forms.TextInput(attrs={"class": "form-control"}),

            "montant_ht": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "taux_tva": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remise": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "montant_paye": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),

            "note_client": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "note_interne": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        params = ParametreFacture.objects.first()

        self.fields["type_piece"].initial = "DEVIS"

        if not self.instance.pk:
            today = timezone.localdate()

            self.fields["statut"].initial = "BROUILLON"
            self.fields["date_facture"].initial = today
            self.fields["date_colis"].initial = today
            self.fields["poids_kg"].initial = 0
            self.fields["nb_colis"].initial = 1
            self.fields["remise"].initial = 0
            self.fields["montant_paye"].initial = 0

            if params:
                self.fields["devise"].initial = params.devise_defaut
                self.fields["taux_tva"].initial = params.taux_tva_defaut
                self.fields["date_echeance"].initial = today + timezone.timedelta(days=params.delai_paiement_jours)
            else:
                self.fields["devise"].initial = "EUR"
                self.fields["taux_tva"].initial = 0
                self.fields["date_echeance"].initial = today + timezone.timedelta(days=7)

    def clean(self):
        cleaned_data = super().clean()

        montant_ht = cleaned_data.get("montant_ht") or 0
        remise = cleaned_data.get("remise") or 0
        montant_paye = cleaned_data.get("montant_paye") or 0
        date_facture = cleaned_data.get("date_facture")
        date_echeance = cleaned_data.get("date_echeance")

        if montant_ht < 0:
            self.add_error("montant_ht", "Le montant ne peut pas être négatif.")

        if remise > montant_ht:
            self.add_error("remise", "La remise ne peut pas être supérieure au montant HT.")

        if montant_paye < 0:
            self.add_error("montant_paye", "Le montant payé ne peut pas être négatif.")

        if date_facture and date_echeance and date_echeance < date_facture:
            self.add_error("date_echeance", "La date d’échéance ne peut pas être antérieure à la date de facture.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_piece = "DEVIS"

        if commit:
            instance.save()

        return instance
        
        
class BilanFilterForm(forms.Form):
    du = forms.DateField(required=False, widget=forms.DateInput(attrs={"type":"date"}))
    au = forms.DateField(required=False, widget=forms.DateInput(attrs={"type":"date"}))
    agence = forms.ChoiceField(required=False, choices=[("","Toutes"),("PARIS","PARIS"),("ROISSY","ROISSY")])

class BallonForm(forms.ModelForm):
    class Meta:
        model = Ballon
        fields = ["type_ballon", "agence_destination", "code", "commentaire"]
        widgets = {
            "commentaire": forms.TextInput(attrs={"placeholder": "Note (facultatif)"}),
        }

class BallonItemForm(forms.ModelForm):
    class Meta:
        model = BallonItem
        fields = ["reference", "poids_kg"]
        widgets = {
            "reference": forms.TextInput(attrs={"placeholder": "Réf dossier ex: BA1176-1"}),
        }

class SMSMessageForm(forms.ModelForm):
    class Meta:
        model = SMSMessage
        fields = ["titre", "message", "liste_telephones"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3}),
            "liste_telephones": forms.Textarea(attrs={"rows": 2}),
        }


class TransfertArgentForm(forms.ModelForm):
    class Meta:
        model = TransfertArgent
        fields = [
            "statut",
            "agent_nom",
            "expediteur_nom",
            "expediteur_tel",
            "destinataire_nom",
            "destinataire_tel",
            "devise_envoi",
            "montant_envoye",
            "taux_transfert",
            "devise_reception",
            "montant_total_payer",
            "montant_reception",
            "date_transfert",
            "date_retrait",
            "description",
        ]
        widgets = {
            "statut": forms.Select(attrs={"class": "form-select"}),
            "agent_nom": forms.TextInput(attrs={"class": "form-control"}),
            "expediteur_nom": forms.TextInput(attrs={"class": "form-control"}),
            "expediteur_tel": forms.TextInput(attrs={"class": "form-control"}),
            "destinataire_nom": forms.TextInput(attrs={"class": "form-control"}),
            "destinataire_tel": forms.TextInput(attrs={"class": "form-control"}),

            "devise_envoi": forms.Select(attrs={"class": "form-select"}),
            "montant_envoye": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "id": "id_montant_envoye",
            }),
            "taux_transfert": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "id": "id_taux_transfert",
            }),
            "devise_reception": forms.Select(attrs={
                "class": "form-select",
                "id": "id_devise_reception",
            }),

            "montant_total_payer": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "readonly": "readonly",
                "id": "id_montant_total_payer",
            }),
            "montant_reception": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "readonly": "readonly",
                "id": "id_montant_reception",
            }),

            "date_transfert": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_retrait": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "statut": "Statut",
            "agent_nom": "Nom de l’agent",
            "expediteur_nom": "Expéditeur",
            "expediteur_tel": "Tél. expéditeur",
            "destinataire_nom": "Destinataire",
            "destinataire_tel": "Tél. destinataire",
            "devise_envoi": "Monnaie d’envoi",
            "montant_envoye": "Somme envoyée",
            "taux_transfert": "Taux de transfert",
            "devise_reception": "Monnaie de retrait",
            "montant_total_payer": "Total à payer",
            "montant_reception": "Montant à recevoir",
            "date_transfert": "Date transfert",
            "date_retrait": "Date retrait",
            "description": "Description",
        }
 

class FactureEmailForm(forms.Form):
    email_destinataire = forms.CharField(
        label="Destinataires",
        help_text="Plusieurs adresses séparées par une virgule",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "client@email.com, compta@email.com"
        })
    )
    sujet = forms.CharField(
        label="Sujet",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 8})
    )

    def __init__(self, *args, facture=None, **kwargs):
        super().__init__(*args, **kwargs)

        if facture:
            params = ParametreFacture.objects.first()

            sujet = f"Votre facture {facture.numero}"
            message = "Veuillez trouver votre facture en pièce jointe."

            if params:
                sujet = params.modele_email_sujet.format(
                    type_piece=facture.get_type_piece_display(),
                    numero=facture.numero,
                    entreprise=params.nom_entreprise,
                )
                message = params.modele_email_message.format(
                    client_nom=facture.client_nom_complet or "",
                    type_piece=facture.get_type_piece_display(),
                    numero=facture.numero,
                    ref_colis=facture.ref_colis or "",
                    total_ttc=facture.montant_ttc,
                    devise=facture.devise,
                    entreprise=params.nom_entreprise,
                )

            self.fields["email_destinataire"].initial = facture.client_email_facturation or ""
            self.fields["sujet"].initial = sujet
            self.fields["message"].initial = message

    def clean_email_destinataire(self):
        raw_value = self.cleaned_data["email_destinataire"]
        emails = [e.strip() for e in raw_value.split(",") if e.strip()]
        if not emails:
            raise forms.ValidationError("Ajoute au moins une adresse e-mail.")

        validator = forms.EmailField()
        cleaned = []
        for email in emails:
            validator.clean(email)
            cleaned.append(email)
        return ", ".join(cleaned)