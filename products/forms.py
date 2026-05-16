from decimal import Decimal
from decimal import InvalidOperation as DecimalException

from django import forms

from .models import Category, Product, ProductMovement


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

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

    price = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"}))

    stock = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}))

    class Meta:
        model = Product
        fields = ["categories", "name", "description", "price", "stock", "is_public"]
        widgets = {
            "categories": forms.CheckboxSelectMultiple(attrs={"class": "flex flex-wrap gap-4 p-4 card bg-muted/30"}),
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Product Name"}),
            "description": forms.Textarea(attrs={"class": "input w-full h-32 py-2", "placeholder": "Description"}),
            "stock": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}),
            "is_public": forms.CheckboxInput(attrs={"class": "checkbox", "id": "id_is_public"}),
        }

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        assert stock is not None
        if stock < 0:
            raise forms.ValidationError("Ops! Você não pode ter um estoque menor que zero.")
        return stock

    def clean_price(self):
        price_str = self.cleaned_data.get("price")
        if not price_str:
            return Decimal("0.00")
        try:
            # Remove pontos de milhar e troca vírgula por ponto
            price_numeric = price_str.replace(".", "").replace(",", ".")
            return Decimal(price_numeric)
        except (ValueError, TypeError, DecimalException):
            raise forms.ValidationError("Informe um preço válido (ex: 55,99).") from None


class MovementForm(forms.ModelForm):
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
