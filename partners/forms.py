from django import forms

from products.models import FieldConfig

from .models import Customer, Supplier


def _apply_partner_field_config(form, user, model_name):
    if not user or not user.is_authenticated:
        return
    configs = FieldConfig.objects.filter(user=user, model_name=model_name)
    for config in configs:
        if config.field_name in form.fields:
            form.fields[config.field_name].required = config.required


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _apply_partner_field_config(self, user, "Customer")

    class Meta:
        model = Customer
        fields = ["name", "email", "phone", "cpf", "birth_date", "street", "number", "complement", "neighborhood", "city", "state", "zip_code"]
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
            "street": forms.TextInput(attrs={"class": "input", "placeholder": "Rua"}),
            "number": forms.TextInput(attrs={"class": "input", "placeholder": "Número"}),
            "complement": forms.TextInput(attrs={"class": "input", "placeholder": "Complemento"}),
            "neighborhood": forms.TextInput(attrs={"class": "input", "placeholder": "Bairro"}),
            "city": forms.TextInput(attrs={"class": "input", "placeholder": "Cidade"}),
            "state": forms.TextInput(attrs={"class": "input", "placeholder": "UF"}),
            "zip_code": forms.TextInput(attrs={"class": "input", "placeholder": "CEP"}),
        }


class SupplierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        _apply_partner_field_config(self, user, "Supplier")

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
            "observations",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "inscricao_estadual",
            "inscricao_municipal",
            "regime_tributario",
            "prazo_entrega_medio",
            "condicoes_pagamento_padrao",
            "status",
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
            "observations": forms.Textarea(
                attrs={"class": "input", "rows": 3, "placeholder": "Observações"}
            ),
            "street": forms.TextInput(attrs={"class": "input", "placeholder": "Rua"}),
            "number": forms.TextInput(attrs={"class": "input", "placeholder": "Número"}),
            "complement": forms.TextInput(attrs={"class": "input", "placeholder": "Complemento"}),
            "neighborhood": forms.TextInput(attrs={"class": "input", "placeholder": "Bairro"}),
            "city": forms.TextInput(attrs={"class": "input", "placeholder": "Cidade"}),
            "state": forms.TextInput(attrs={"class": "input", "placeholder": "UF (ex: SP)"}),
            "zip_code": forms.TextInput(attrs={"class": "input", "placeholder": "CEP"}),
            "inscricao_estadual": forms.TextInput(attrs={"class": "input", "placeholder": "Inscrição Estadual"}),
            "inscricao_municipal": forms.TextInput(attrs={"class": "input", "placeholder": "Inscrição Municipal"}),
            "regime_tributario": forms.Select(attrs={"class": "select w-full"}),
            "prazo_entrega_medio": forms.NumberInput(attrs={"class": "input", "placeholder": "Dias"}),
            "condicoes_pagamento_padrao": forms.TextInput(attrs={"class": "input", "placeholder": "Ex: 30/60 dias, boleto"}),
            "status": forms.Select(attrs={"class": "select w-full"}),
        }
