from decimal import Decimal
from decimal import InvalidOperation as DecimalException

from django import forms

from partners.models import Supplier

from .models import Category, FieldConfig, Product, ProductMovement, StorageLocation

FIELD_CONFIG_MAP = {
    "Product": [
        ("name", "Nome"),
        ("description", "Descrição"),
        ("price", "Preço"),
        ("cost_price", "Preço de Custo"),
        ("categories", "Categorias"),
        ("supplier", "Fornecedor"),
        ("is_public", "Público"),
        ("codigo_barras", "Código de Barras"),
        ("sku", "SKU"),
        ("marca", "Marca"),
        ("unidade_medida", "Unidade de Medida"),
        ("peso_liquido", "Peso Líquido"),
        ("peso_bruto", "Peso Bruto"),
        ("largura", "Largura"),
        ("altura", "Altura"),
        ("profundidade", "Profundidade"),
        ("ncm", "NCM"),
        ("cest", "CEST"),
        ("status", "Status"),
    ],
    "Category": [
        ("name", "Nome"),
        ("slug", "Slug"),
        ("description", "Descrição"),
        ("color", "Cor"),
    ],
    "StorageLocation": [
        ("name", "Nome"),
        ("type", "Tipo"),
        ("description", "Descrição"),
        ("is_active", "Ativo"),
    ],
    "Customer": [
        ("name", "Nome"),
        ("email", "Email"),
        ("phone", "Telefone"),
        ("cpf", "CPF"),
        ("birth_date", "Data de Nascimento"),
        ("street", "Rua"),
        ("number", "Número"),
        ("complement", "Complemento"),
        ("neighborhood", "Bairro"),
        ("city", "Cidade"),
        ("state", "Estado"),
        ("zip_code", "CEP"),
    ],
    "Supplier": [
        ("name", "Nome"),
        ("company_name", "Razão Social"),
        ("cnpj", "CNPJ"),
        ("email", "Email"),
        ("phone", "Telefone"),
        ("contact_person", "Pessoa de Contato"),
        ("website", "Website"),
        ("observations", "Observações"),
        ("street", "Rua"),
        ("number", "Número"),
        ("complement", "Complemento"),
        ("neighborhood", "Bairro"),
        ("city", "Cidade"),
        ("state", "Estado"),
        ("zip_code", "CEP"),
        ("inscricao_estadual", "Inscrição Estadual"),
        ("inscricao_municipal", "Inscrição Municipal"),
        ("regime_tributario", "Regime Tributário"),
        ("prazo_entrega_medio", "Prazo de Entrega Médio"),
        ("condicoes_pagamento_padrao", "Condições de Pagamento"),
        ("status", "Status"),
    ],
    "ProductMovement": [
        ("quantity", "Quantidade"),
        ("reason", "Motivo"),
    ],
}


def apply_field_config(form, user, model_name):
    if not user or not user.is_authenticated:
        return
    configs = FieldConfig.objects.filter(user=user, model_name=model_name)
    for config in configs:
        if config.field_name in form.fields:
            form.fields[config.field_name].required = config.required


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.user = user
        apply_field_config(self, user, "Category")

    class Meta:
        model = Category
        fields = ["name", "slug", "description", "color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Nome da Categoria"}),
            "slug": forms.TextInput(attrs={"class": "input w-full", "placeholder": "slug-da-categoria"}),
            "description": forms.Textarea(attrs={"class": "input w-full h-24 py-2", "placeholder": "Descrição"}),
            "color": forms.TextInput(attrs={"class": "input w-full h-10", "type": "color"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if self.user and Category.objects.filter(user=self.user, slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Você já possui uma categoria com este slug.")
        return slug


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["categories"].queryset = Category.objects.filter(user=user)
            self.fields["supplier"].queryset = Supplier.objects.filter(user=user)
        apply_field_config(self, user, "Product")

        if self.instance and self.instance.pk:
            if self.instance.price is not None:
                self.initial["price"] = f"{self.instance.price:.2f}".replace(".", ",")
            if self.instance.cost_price is not None:
                self.initial["cost_price"] = f"{self.instance.cost_price:.2f}".replace(".", ",")

    price = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"}))
    cost_price = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"}))

    class Meta:
        model = Product
        fields = [
            "categories", "name", "description", "price", "cost_price",
            "supplier", "is_public",
            "codigo_barras", "sku", "marca", "unidade_medida",
            "peso_liquido", "peso_bruto", "largura", "altura", "profundidade",
            "ncm", "cest", "status",
        ]
        widgets = {
            "categories": forms.CheckboxSelectMultiple(attrs={"class": "flex flex-wrap gap-4 p-4 card bg-muted/30"}),
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Nome do Produto"}),
            "description": forms.Textarea(attrs={"class": "input w-full h-32 py-2", "placeholder": "Descrição"}),
            "supplier": forms.Select(attrs={"class": "select w-full"}),
            "is_public": forms.CheckboxInput(attrs={"class": "checkbox", "id": "id_is_public"}),
            "codigo_barras": forms.TextInput(attrs={"class": "input w-full", "placeholder": "EAN/GTIN"}),
            "sku": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Código interno"}),
            "marca": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Marca do produto"}),
            "unidade_medida": forms.Select(attrs={"class": "select w-full"}),
            "peso_liquido": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "kg", "step": "0.001"}),
            "peso_bruto": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "kg", "step": "0.001"}),
            "largura": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "cm", "step": "0.01"}),
            "altura": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "cm", "step": "0.01"}),
            "profundidade": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "cm", "step": "0.01"}),
            "ncm": forms.TextInput(attrs={"class": "input w-full", "placeholder": "NCM (8 dígitos)"}),
            "cest": forms.TextInput(attrs={"class": "input w-full", "placeholder": "CEST (7 dígitos)"}),
            "status": forms.Select(attrs={"class": "select w-full"}),
        }

    def clean_price(self):
        price_str = self.cleaned_data.get("price")
        if not price_str:
            return Decimal("0.00")
        try:
            price_numeric = price_str.replace(".", "").replace(",", ".")
            return Decimal(price_numeric)
        except (ValueError, TypeError, DecimalException):
            raise forms.ValidationError("Informe um preço válido (ex: 55,99).") from None

    def clean_cost_price(self):
        cost_str = self.cleaned_data.get("cost_price")
        if not cost_str:
            return Decimal("0.00")
        try:
            cost_numeric = cost_str.replace(".", "").replace(",", ".")
            return Decimal(cost_numeric)
        except (ValueError, TypeError, DecimalException):
            raise forms.ValidationError("Informe um preço de custo válido (ex: 55,99).") from None


class StorageLocationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        apply_field_config(self, user, "StorageLocation")

    class Meta:
        model = StorageLocation
        fields = ["name", "type", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Nome do local"}),
            "type": forms.Select(attrs={"class": "select w-full"}),
            "description": forms.Textarea(attrs={"class": "input w-full h-24 py-2", "placeholder": "Descrição (opcional)"}),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }


class MovementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        apply_field_config(self, user, "ProductMovement")

    class Meta:
        model = ProductMovement
        fields = ["quantity", "reason"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"class": "input w-full", "min": "1", "placeholder": "Quantidade"}),
            "reason": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Motivo (opcional)"}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None or quantity <= 0:
            raise forms.ValidationError("A quantidade deve ser maior que zero.")
        return quantity
