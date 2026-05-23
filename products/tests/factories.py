import random
import string
from decimal import Decimal

from django.contrib.auth.models import User

from products.models import Category, PriceHistory, Product, Profile


def get_random_string(length=10):
    """Generate random string for unique values"""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class UserFactory:
    _counter = 0

    @classmethod
    def create(cls, **kwargs):
        cls._counter += 1
        defaults = {
            "username": f"testuser{cls._counter}",
            "email": f"test{cls._counter}@example.com",
            "password": "testpass123",
        }
        defaults.update(kwargs)
        user = User.objects.create_user(**defaults)
        Profile.objects.get_or_create(user=user)
        return user

    @classmethod
    def create_admin(cls):
        """Create admin user with provided credentials"""
        user = User.objects.create_user(
            username="admin", email="admin@admin.com", password="Adm@1adn!!!"
        )
        Profile.objects.get_or_create(user=user)
        return user


class CategoryFactory:
    _counter = 0

    @classmethod
    def create(cls, **kwargs):
        cls._counter += 1
        suffix = get_random_string(5)
        user = kwargs.pop("user", UserFactory.create())
        defaults = {
            "user": user,
            "name": f"Test Category {cls._counter}",
            "slug": f"test-category-{cls._counter}-{suffix}",
            "description": "Test description",
            "color": "#3b82f6",
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)


class ProductFactory:
    _counter = 0

    @classmethod
    def create(cls, **kwargs):
        cls._counter += 1
        user = kwargs.pop("user", UserFactory.create())
        stock_qty = kwargs.pop("stock", 0)
        defaults = {
            "user": user,
            "name": f"Test Product {cls._counter}",
            "description": "Test description",
            "price": Decimal("10.00"),
            "is_public": False,
        }
        defaults.update(kwargs)
        product = Product.objects.create(**defaults)

        # Add categories if provided
        if "categories" in kwargs:
            product.categories.set(kwargs["categories"])

        if stock_qty > 0:
            from products.models import Stock, StorageLocation
            local = StorageLocation.objects.filter(user=user).first()
            if not local:
                local = StorageLocation.objects.create(user=user, name="Depósito Principal")
            Stock.objects.create(product=product, local=local, quantidade_atual=stock_qty)

        return product


class PriceHistoryFactory:
    _counter = 0

    @classmethod
    def create(cls, **kwargs):
        cls._counter += 1
        product = kwargs.pop("product", ProductFactory.create())
        defaults = {"product": product, "price": Decimal("10.00")}
        defaults.update(kwargs)
        return PriceHistory.objects.create(**defaults)
