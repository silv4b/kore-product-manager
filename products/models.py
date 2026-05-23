from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

if TYPE_CHECKING:
    from .models import PriceHistory, ProductMovement


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories", null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3b82f6")  # Hex color para UI

    class Meta:
        verbose_name_plural = "Categories"
        constraints = [models.UniqueConstraint(fields=["user", "slug"], name="unique_user_slug")]

    def __str__(self):
        return self.name


class ProductManager(models.Manager):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(user=user)

    def public(self):
        return self.filter(is_public=True)

    def low_stock(self):
        return self.filter(
            pk__in=Stock.objects.annotate(
                diff=models.F("quantidade_atual") - models.F("estoque_minimo")
            ).filter(diff__lte=0).values("product")
        )

    def with_stock_annotations(self):
        return self.annotate(
            _stock_value=models.Subquery(
                Stock.objects.filter(product=models.OuterRef("pk"))
                .values("product")
                .annotate(total=models.Sum("quantidade_atual"))
                .values("total")[:1]
            ),
            _min_stock_value=models.Subquery(
                Stock.objects.filter(product=models.OuterRef("pk"))
                .values("product")
                .annotate(total=models.Sum("estoque_minimo"))
                .values("total")[:1]
            ),
        )


class Product(models.Model):
    class StatusChoices(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"
        DESCONTINUADO = "descontinuado", "Descontinuado"

    class UnidadeMedidaChoices(models.TextChoices):
        UN = "UN", "Unidade"
        KG = "KG", "Quilograma"
        CX = "CX", "Caixa"
        L = "L", "Litro"
        PCT = "PCT", "Pacote"

    # 1. Campos do Banco de Dados Primeiro
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    supplier = models.ForeignKey("partners.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    codigo_barras = models.CharField(max_length=14, blank=True, default="", verbose_name="Código de Barras (EAN/GTIN)")
    sku = models.CharField(max_length=50, blank=True, default="", verbose_name="SKU (Código Interno)")
    marca = models.CharField(max_length=100, blank=True, default="", verbose_name="Marca")
    unidade_medida = models.CharField(
        max_length=3, choices=UnidadeMedidaChoices.choices, blank=True, default=UnidadeMedidaChoices.UN, verbose_name="Unidade de Medida"
    )
    peso_liquido = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Peso Líquido (kg)")
    peso_bruto = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, verbose_name="Peso Bruto (kg)")
    largura = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Largura (cm)")
    altura = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Altura (cm)")
    profundidade = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Profundidade (cm)")
    ncm = models.CharField(max_length=8, blank=True, default="", verbose_name="NCM")
    cest = models.CharField(max_length=9, blank=True, default="", verbose_name="CEST")
    status = models.CharField(max_length=14, choices=StatusChoices.choices, blank=True, default=StatusChoices.ATIVO, verbose_name="Status")
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 2. Managers vêm logo após os campos
    objects = ProductManager()

    # Como price_history é injetado em Product com <related_name="price_history">.
    # Isso avisa ao linter que price_history de fato existe em Product.
    if TYPE_CHECKING:
        price_history: models.Manager["PriceHistory"]

    # 3. Métodos do modelo por último
    def __str__(self):
        return self.name

    @property
    def stock(self):
        try:
            return self._stock_value
        except AttributeError:
            total = self.stocks.aggregate(total=models.Sum("quantidade_atual"))["total"]
            return total or 0

    @property
    def min_stock_level(self):
        try:
            return self._min_stock_value
        except AttributeError:
            total = self.stocks.aggregate(total=models.Sum("estoque_minimo"))["total"]
            return total or 0

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 100.00 if self.price > 0 else 0.00

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock_level


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Price Histories"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.product.name} - R$ {self.price} em {self.changed_at.strftime('%d/%m/%Y %H:%M')}"


class ProductMovement(models.Model):
    MOVEMENT_TYPES = [
        ("IN", "Entrada"),
        ("OUT", "Saída"),
    ]

    # Campos do Banco de Dados
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    type = models.CharField(max_length=3, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    moved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Movements"
        ordering = ["-moved_at"]

    # 3. Type Checking para o Pylance parar de reclamar
    if TYPE_CHECKING:

        def get_type_display(self) -> str: ...

    # 4. Métodos da classe
    def __str__(self):
        display_type = self.get_type_display()
        moved = self.moved_at.strftime("%d/%m/%Y %H:%M")
        return f"{display_type} - {self.product.name} ({self.quantity}) em {moved}"


class FieldConfig(models.Model):
    MODEL_CHOICES = [
        ("Product", "Produto"),
        ("Category", "Categoria"),
        ("StorageLocation", "Local de Armazenamento"),
        ("Customer", "Cliente"),
        ("Supplier", "Fornecedor"),
        ("ProductMovement", "Movimentação"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="field_configs")
    model_name = models.CharField(max_length=50, choices=MODEL_CHOICES, verbose_name="Formulário")
    field_name = models.CharField(max_length=100, verbose_name="Campo")
    field_label = models.CharField(max_length=200, blank=True, default="", verbose_name="Rótulo")
    required = models.BooleanField(default=False, verbose_name="Obrigatório")

    class Meta:
        verbose_name = "Configuração de Campo"
        verbose_name_plural = "Configurações de Campos"
        unique_together = [["user", "model_name", "field_name"]]

    def __str__(self):
        return f"{self.get_model_name_display()} / {self.field_label or self.field_name}: {'Obrigatório' if self.required else 'Opcional'}"


class Profile(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    view_preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class StorageLocation(models.Model):
    class TypeChoices(models.TextChoices):
        DEPOSITO = "deposito", "Depósito"
        LOJA = "loja", "Loja"
        CORREDOR = "corredor", "Corredor"
        PRATELEIRA = "prateleira", "Prateleira"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="storage_locations")
    name = models.CharField(max_length=100, verbose_name="Nome")
    type = models.CharField(max_length=20, choices=TypeChoices.choices, default=TypeChoices.DEPOSITO, verbose_name="Tipo")
    description = models.TextField(blank=True, default="", verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Local de Armazenamento"
        verbose_name_plural = "Locais de Armazenamento"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stocks")
    local = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name="stocks")
    quantidade_atual = models.IntegerField(default=0, verbose_name="Quantidade Atual")
    quantidade_reservada = models.IntegerField(default=0, verbose_name="Quantidade Reservada")
    estoque_minimo = models.IntegerField(default=0, verbose_name="Estoque Mínimo")
    estoque_maximo = models.IntegerField(null=True, blank=True, verbose_name="Estoque Máximo")
    lote = models.CharField(max_length=50, blank=True, default="", verbose_name="Lote")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Data de Validade")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Estoque"
        verbose_name_plural = "Estoques"
        unique_together = [["product", "local"]]

    def __str__(self):
        return f"{self.product.name} - {self.local.name}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


@receiver(user_logged_in)
def load_user_theme(sender, request, user, **kwargs):
    if hasattr(user, "profile"):
        request.session["theme"] = user.profile.theme


@receiver(post_save, sender=Product)
def track_price_changes(sender, instance, created, **kwargs):
    """
    Registra automaticamente mudanças de preço no histórico.
    Cria um registro inicial quando o produto é criado.
    """
    if created:
        PriceHistory.objects.create(product=instance, price=instance.price)
    else:
        last_price_entry = instance.price_history.first()

        if not last_price_entry:
            PriceHistory.objects.create(product=instance, price=instance.price)
        elif last_price_entry.price != instance.price:
            PriceHistory.objects.create(product=instance, price=instance.price)


@receiver(post_save, sender=Stock)
def track_stock_changes(sender, instance, created, **kwargs):
    """
    Registra automaticamente mudanças de estoque no histórico de movimentações.
    Cria um registro inicial quando o estoque é criado.
    """
    from django.db.models import Case, IntegerField, Sum, When

    if created:
        if instance.quantidade_atual > 0:
            ProductMovement.objects.create(
                product=instance.product,
                type="IN",
                quantity=instance.quantidade_atual,
                reason="Estoque inicial",
            )
    else:
        movements_sum = (
            instance.product.movements.aggregate(
                total=Sum(
                    Case(
                        When(type="IN", then=models.F("quantity")),
                        When(type="OUT", then=-models.F("quantity")),
                        default=0,
                        output_field=IntegerField(),
                    )
                )
            )["total"]
            or 0
        )

        diff = instance.quantidade_atual - movements_sum

        if diff > 0:
            ProductMovement.objects.create(product=instance.product, type="IN", quantity=diff, reason="Ajuste de estoque")
        elif diff < 0:
            ProductMovement.objects.create(
                product=instance.product,
                type="OUT",
                quantity=abs(diff),
                reason="Ajuste de estoque",
            )


@receiver(post_save, sender=User)
def create_default_storage_location(sender, instance, created, **kwargs):
    if created:
        StorageLocation.objects.get_or_create(
            user=instance,
            name="Depósito Principal",
            defaults={"type": StorageLocation.TypeChoices.DEPOSITO},
        )


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        from django.utils.text import slugify

        default_categories = ["Eletronicos", "Importados", "Nacionais", "Utensilios"]
        for cat_name in default_categories:
            Category.objects.get_or_create(
                user=instance,
                name=cat_name,
                defaults={
                    "slug": slugify(cat_name),
                    "description": f"Categoria padrao: {cat_name}",
                },
            )
