from django import forms
from decimal import Decimal, InvalidOperation as DecimalException
from .models import Product, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "description", "color"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input w-full", "placeholder": "Nome da Categoria"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "input w-full", "placeholder": "slug-da-categoria"}
            ),
            "description": forms.Textarea(
                attrs={"class": "input w-full h-24 py-2", "placeholder": "Descrição"}
            ),
            "color": forms.TextInput(
                attrs={"class": "input w-full h-10", "type": "color"}
            ),
        }


class ProductForm(forms.ModelForm):
    price = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"})
    )

    class Meta:
        model = Product
        fields = ["categories", "name", "description", "price", "stock", "is_public"]
        widgets = {
            "categories": forms.CheckboxSelectMultiple(
                attrs={"class": "flex flex-wrap gap-4 p-4 card bg-muted/30"}
            ),
            "name": forms.TextInput(
                attrs={"class": "input w-full", "placeholder": "Product Name"}
            ),
            "description": forms.Textarea(
                attrs={"class": "input w-full h-32 py-2", "placeholder": "Description"}
            ),
            "stock": forms.NumberInput(
                attrs={"class": "input w-full", "placeholder": "0"}
            ),
            "is_public": forms.CheckboxInput(
                attrs={"class": "checkbox", "id": "id_is_public"}
            ),
        }

    def clean_price(self):
        price_str = self.cleaned_data.get("price")
        if not price_str:
            return Decimal("0.00")
        try:
            # Remove pontos de milhar e troca vírgula por ponto
            price_numeric = price_str.replace(".", "").replace(",", ".")
            return Decimal(price_numeric)
        except (ValueError, TypeError, DecimalException):
            raise forms.ValidationError("Informe um preço válido (ex: 55,99).")
