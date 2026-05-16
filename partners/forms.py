from django import forms

from .models import Customer, Supplier


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email", "phone", "cpf", "birth_date", "address"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Nome completo"}
            ),
            "email": forms.EmailInput(attrs={"class": "input", "placeholder": "Email"}),
            "phone": forms.TextInput(
                attrs={"class": "input", "placeholder": "Telefone"}
            ),
            "cpf": forms.TextInput(attrs={"class": "input", "placeholder": "CPF"}),
            "birth_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "address": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 3,
                    "placeholder": "Endereço completo",
                }
            ),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "company_name",
            "cnpj",
            "email",
            "phone",
            "contact_person",
            "website",
            "address",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Nome fantasia / Nome"}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Razão Social"}
            ),
            "cnpj": forms.TextInput(attrs={"class": "input", "placeholder": "CNPJ"}),
            "email": forms.EmailInput(attrs={"class": "input", "placeholder": "Email"}),
            "phone": forms.TextInput(
                attrs={"class": "input", "placeholder": "Telefone"}
            ),
            "contact_person": forms.TextInput(
                attrs={"class": "input", "placeholder": "Pessoa de contato"}
            ),
            "website": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://..."}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "input",
                    "rows": 3,
                    "placeholder": "Endereço completo",
                }
            ),
        }
