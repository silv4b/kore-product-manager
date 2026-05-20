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


class Supplier(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="suppliers", null=True, blank=True)
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=255, blank=True, default="")
    observations = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

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
        return self.filter(stock__lte=models.F("min_stock_level"))


class Product(models.Model):
    # 1. Campos do Banco de Dados Primeiro
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products", null=True, blank=True)
    supplier = models.ForeignKey("Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    categories = models.ManyToManyField(
        Category,
        related_name="products",
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=0)
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
        # Primeiro registro de preço ao criar o produto
        PriceHistory.objects.create(product=instance, price=instance.price)
    else:
        # Verifica se o preço mudou comparando com o último registro
        last_price_entry = instance.price_history.first()

        # Se não há histórico anterior, cria o primeiro registro
        if not last_price_entry:
            PriceHistory.objects.create(product=instance, price=instance.price)
        # Se o preço mudou, cria um novo registro
        elif last_price_entry.price != instance.price:
            PriceHistory.objects.create(product=instance, price=instance.price)


@receiver(post_save, sender=Product)
def track_stock_changes(sender, instance, created, **kwargs):
    """
    Registra automaticamente mudanças de estoque no histórico de movimentações.
    Cria um registro inicial quando o produto é criado.
    """
    if created:
        # Primeiro registro de estoque (Entrada) ao criar o produto
        if instance.stock > 0:
            ProductMovement.objects.create(
                product=instance,
                type="IN",
                quantity=instance.stock,
                reason="Registro inicial do produto",
            )
    else:
        # Verifica se o estoque mudou comparando com o último estado conhecido
        # Precisamos saber o estoque anterior. Como o Django não guarda o estado anterior nativamente no save,
        # poderíamos usar um middleware ou buscar o último registro de movimentação para calcular.
        # Mas uma forma mais simples é ver o saldo acumulado das movimentações.
        # No entanto, se o usuário editar o campo 'stock' livremente, queremos capturar a diferença.

        from django.db.models import Sum

        movements_sum = (
            instance.movements.aggregate(
                total=Sum(
                    models.Case(
                        models.When(type="IN", then=models.F("quantity")),
                        models.When(type="OUT", then=-models.F("quantity")),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                )
            )["total"]
            or 0
        )

        diff = instance.stock - movements_sum

        if diff > 0:
            ProductMovement.objects.create(product=instance, type="IN", quantity=diff, reason="Ajuste de estoque")
        elif diff < 0:
            ProductMovement.objects.create(
                product=instance,
                type="OUT",
                quantity=abs(diff),
                reason="Ajuste de estoque",
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
