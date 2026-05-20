from decimal import Decimal
from decimal import InvalidOperation as DecimalException

from django import forms

from .models import Category, Product, ProductMovement, Supplier


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


class SupplierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Supplier
        fields = ["name", "contact", "observations"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Nome do Fornecedor"}),
            "contact": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Contato (Telefone, E-mail, etc.)"}),
            "observations": forms.Textarea(attrs={"class": "input w-full h-24 py-2", "placeholder": "Observações"}),
        }


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["categories"].queryset = Category.objects.filter(user=user)
            self.fields["supplier"].queryset = Supplier.objects.filter(user=user)

        if self.instance and self.instance.pk:
            if self.instance.price is not None:
                self.initial["price"] = f"{self.instance.price:.2f}".replace(".", ",")
            if self.instance.cost_price is not None:
                self.initial["cost_price"] = f"{self.instance.cost_price:.2f}".replace(".", ",")

    price = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"}))
    cost_price = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "0,00"}))
    stock = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}))
    min_stock_level = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}))

    class Meta:
        model = Product
        fields = ["categories", "name", "description", "price", "cost_price", "stock", "min_stock_level", "supplier", "is_public"]
        widgets = {
            "categories": forms.CheckboxSelectMultiple(attrs={"class": "flex flex-wrap gap-4 p-4 card bg-muted/30"}),
            "name": forms.TextInput(attrs={"class": "input w-full", "placeholder": "Nome do Produto"}),
            "description": forms.Textarea(attrs={"class": "input w-full h-32 py-2", "placeholder": "Descrição"}),
            "stock": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}),
            "min_stock_level": forms.NumberInput(attrs={"class": "input w-full", "placeholder": "0"}),
            "supplier": forms.Select(attrs={"class": "select w-full"}),
            "is_public": forms.CheckboxInput(attrs={"class": "checkbox", "id": "id_is_public"}),
        }

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is None:
            raise forms.ValidationError("O campo de estoque é obrigatório.")
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

    def clean_cost_price(self):
        cost_str = self.cleaned_data.get("cost_price")
        if not cost_str:
            return Decimal("0.00")
        try:
            cost_numeric = cost_str.replace(".", "").replace(",", ".")
            return Decimal(cost_numeric)
        except (ValueError, TypeError, DecimalException):
            raise forms.ValidationError("Informe um preço de custo válido (ex: 55,99).") from None

    def clean_min_stock_level(self):
        min_stock = self.cleaned_data.get("min_stock_level")
        if min_stock is None:
            return 0
        if min_stock < 0:
            raise forms.ValidationError("O estoque mínimo não pode ser menor que zero.")
        return min_stock


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
