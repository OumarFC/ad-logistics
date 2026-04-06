from django import forms
from gestion.models import Client


class EnvoyerSMSForm(forms.Form):
    clients = forms.ModelMultipleChoiceField(
        queryset=Client.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sélectionner des clients"
    )

    numeros = forms.CharField(
        required=False,
        label="Autres numéros",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Un numéro par ligne ou séparés par virgule"
        }),
        help_text="Optionnel : ajoute ici d'autres numéros."
    )

    message = forms.CharField(
        label="Message",
        max_length=500,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "maxlength": 500,
            "placeholder": "Votre message SMS..."
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["clients"].queryset = Client.objects.exclude(
            telephone__isnull=True
        ).exclude(
            telephone__exact=""
        ).order_by("nom")

    def clean(self):
        cleaned = super().clean()
        clients = cleaned.get("clients")
        numeros = cleaned.get("numeros", "")

        if not clients and not numeros.strip():
            raise forms.ValidationError(
                "Sélectionnez au moins un client ou saisissez au moins un numéro."
            )

        return cleaned

    def get_all_numbers(self):
        clients = self.cleaned_data.get("clients")
        raw_numeros = self.cleaned_data.get("numeros", "")

        numbers = []

        if clients:
            for client in clients:
                if client.telephone:
                    numbers.append({
                        "numero": client.telephone,
                        "client_nom": getattr(client, "nom", str(client)),
                    })

        if raw_numeros:
            text = raw_numeros.replace(",", "\n").replace(";", "\n")
            for n in [x.strip() for x in text.splitlines() if x.strip()]:
                numbers.append({
                    "numero": n,
                    "client_nom": "",
                })

        # Déduplication
        seen = set()
        result = []
        for item in numbers:
            key = item["numero"].replace(" ", "")
            if key not in seen:
                seen.add(key)
                result.append(item)

        return result

class SMSLogEditForm(forms.Form):
    numero = forms.CharField(
        label="Numéro",
        max_length=30,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ex: +33789280108"
        })
    )

    message = forms.CharField(
        label="Message",
        max_length=500,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
            "maxlength": 500,
            "placeholder": "Votre message SMS..."
        })
    )