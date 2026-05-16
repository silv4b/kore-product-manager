from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from products.models import Category, PriceHistory, Product, Profile
from products.tests.factories import (
    CategoryFactory,
    PriceHistoryFactory,
    ProductFactory,
    UserFactory,
)


class CategoryModelTest(TestCase):
    """
    Testa o modelo Category (Categoria).
    Verifica criação, slug único por usuário e categorias padrão.
    """

    def test_category_creation(self):
        """
        Testa a criação de uma categoria com todos os campos.
        Verifica que todos os atributos são salvos corretamente.
        """
        category = CategoryFactory.create(
            name="My Electronics",
            slug="my-electronics",
            description="Electronic products",
            color="#ff0000",
        )

        self.assertEqual(category.name, "My Electronics")
        self.assertEqual(category.slug, "my-electronics")
        self.assertEqual(category.description, "Electronic products")
        self.assertEqual(category.color, "#ff0000")
        self.assertEqual(str(category), "My Electronics")

    def test_category_verbose_name_plural(self):
        """
        Testa que o nome plural verbose da categoria está configurado corretamente.
        """
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")

    def test_category_unique_slug_per_user(self):
        """
        Testa que o slug deve ser único para cada usuário.
        Verifica que dois usuários não podem ter categorias com o mesmo slug.
        """
        user = UserFactory.create()
        CategoryFactory.create(user=user, slug="test-slug")
        with self.assertRaises(IntegrityError):
            CategoryFactory.create(user=user, slug="test-slug")

    def test_category_duplicate_slug_different_users(self):
        """
        Testa que diferentes usuários podem ter o mesmo slug.
        Verifica que a restrição de unicidade é por usuário, não global.
        """
        user1 = UserFactory.create()
        user2 = UserFactory.create()

        c1 = CategoryFactory.create(user=user1, slug="t-slug")
        c2 = CategoryFactory.create(user=user2, slug="t-slug")

        self.assertEqual(c1.slug, c2.slug)
        self.assertNotEqual(c1.pk, c2.pk)

    def test_default_categories_creation(self):
        """
        Testa que categorias padrão são criadas automaticamente para novos usuários.
        Verifica a criação das 4 categorias padrão.
        """
        user = UserFactory.create()
        # Default categories: "Eletrônicos", "Importados", "Nacionais", "Utensilios"
        self.assertEqual(Category.objects.filter(user=user).count(), 4)
        slugs = list(Category.objects.filter(user=user).values_list("slug", flat=True))
        self.assertIn("eletronicos", slugs)
        self.assertIn("importados", slugs)


class ProductModelTest(TestCase):
    """
    Testa o modelo Product (Produto).
    Verifica criação, relacionamentos e filtragem por status público.
    """

    def setUp(self):
        self.user = UserFactory.create()
        self.category = CategoryFactory.create(user=self.user)

    def test_product_creation(self):
        """
        Testa a criação de um produto com todos os campos.
        Verifica que todos os atributos são salvos corretamente.
        """
        product = ProductFactory.create(
            user=self.user,
            name="Laptop",
            description="High performance laptop",
            price=Decimal("999.99"),
            stock=5,
            is_public=True,
        )
        product.categories.add(self.category)

        self.assertEqual(product.user, self.user)
        self.assertEqual(product.name, "Laptop")
        self.assertEqual(product.description, "High performance laptop")
        self.assertEqual(product.price, Decimal("999.99"))
        self.assertEqual(product.stock, 5)
        self.assertTrue(product.is_public)
        self.assertIn(self.category, product.categories.all())
        self.assertEqual(str(product), "Laptop")

    def test_product_default_values(self):
        """
        Testa os valores padrão de um produto.
        Verifica que stock é 0 e is_public é False por padrão.
        """
        product = ProductFactory.create()

        self.assertEqual(product.stock, 0)
        self.assertFalse(product.is_public)

    def test_product_user_relationship(self):
        """
        Testa o relacionamento entre produto e usuário.
        Verifica que um produto pertence ao usuário que o criou.
        """
        product = ProductFactory.create(user=self.user)

        self.assertEqual(product.user, self.user)
        self.assertIn(product, self.user.products.all())  # type: ignore

    def test_product_category_relationship(self):
        """
        Testa o relacionamento many-to-many entre produtos e categorias.
        Verifica que um produto pode pertencer a várias categorias.
        """
        category1 = CategoryFactory.create(name="Category 1")
        category2 = CategoryFactory.create(name="Category 2")

        product = ProductFactory.create()
        product.categories.add(category1, category2)

        self.assertIn(product, category1.products.all())  # type: ignore
        self.assertIn(product, category2.products.all())  # type: ignore
        self.assertEqual(product.categories.count(), 2)

    def test_product_public_filtering(self):
        """
        Testa a filtragem de produtos por status público.
        Verifica que produtos públicos e privados são filtrados corretamente.
        """
        public_product = ProductFactory.create(is_public=True)
        private_product = ProductFactory.create(is_public=False)

        public_products = Product.objects.filter(is_public=True)
        private_products = Product.objects.filter(is_public=False)

        self.assertIn(public_product, public_products)
        self.assertNotIn(private_product, public_products)
        self.assertIn(private_product, private_products)
        self.assertNotIn(public_product, private_products)


class PriceHistoryModelTest(TestCase):
    """
    Testa o modelo PriceHistory (Histórico de Preços).
    Verifica criação, ordenação e relacionamentos.
    """

    def setUp(self):
        self.product = ProductFactory.create(price=Decimal("100.00"))

    def test_price_history_creation(self):
        """
        Testa a criação de um registro de histórico de preços.
        Verifica que o preço e a data de alteração são salvos corretamente.
        """
        history = PriceHistoryFactory.create(product=self.product, price=Decimal("150.00"))

        self.assertEqual(history.product, self.product)
        self.assertEqual(history.price, Decimal("150.00"))
        self.assertIsNotNone(history.changed_at)

    def test_price_history_string_representation(self):
        """
        Testa a representação em string do histórico de preços.
        Verifica o formato esperado da string de representação.
        """
        history = PriceHistoryFactory.create(product=self.product, price=Decimal("99.99"))

        expected = f"{self.product.name} - R$ 99.99 em {history.changed_at.strftime('%d/%m/%Y %H:%M')}"
        self.assertEqual(str(history), expected)

    def test_price_history_ordering(self):
        """
        Testa que o histórico de preços é ordenado por changed_at decrescente.
        Verifica que as entradas mais recentes aparecem primeiro.
        """
        import time

        # The product already has one price history entry from creation
        # Create additional history entries with slight delay
        time.sleep(0.01)
        PriceHistoryFactory.create(product=self.product, price=Decimal("50.00"))
        time.sleep(0.01)
        new_history = PriceHistoryFactory.create(product=self.product, price=Decimal("75.00"))

        histories = PriceHistory.objects.all()
        # Should be ordered by changed_at descending (newest first)
        self.assertEqual(histories.first(), new_history)
        # The oldest (original from product creation) should be last
        original_history = histories.last()
        self.assertEqual(
            original_history.price,
            Decimal("100.00"),  # type: ignore
        )  # Original product price

    def test_price_history_verbose_name_plural(self):
        """
        Testa que o nome plural verbose do histórico de preços está correto.
        """
        self.assertEqual(PriceHistory._meta.verbose_name_plural, "Price Histories")

    def test_price_history_product_relationship(self):
        """
        Testa o relacionamento entre histórico de preços e produto.
        Verifica que o histórico pertence ao produto correto.
        """
        history = PriceHistoryFactory.create(product=self.product)

        self.assertEqual(history.product, self.product)
        self.assertIn(history, self.product.price_history.all())


class ProfileModelTest(TestCase):
    """
    Testa o modelo Profile (Perfil de Usuário).
    Verifica criação automática, tema e preferências de visualização.
    """

    def setUp(self):
        self.user = UserFactory.create()

    def test_profile_creation(self):
        """
        Testa a criação automática de perfil quando um usuário é criado.
        Verifica que o perfil é criado via sinal.
        """
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertEqual(self.user.profile.user, self.user)  # type: ignore
        self.assertEqual(self.user.profile.theme, "light")  # type: ignore

    def test_profile_string_representation(self):
        """
        Testa a representação em string do perfil.
        Verifica o formato esperado da string de representação.
        """
        self.user.username = "testuser"
        self.user.save()

        expected = f"{self.user.username}'s profile"
        self.assertEqual(str(self.user.profile), expected)  # type: ignore

    def test_profile_theme_choices(self):
        """
        Testa as opções de tema disponíveis para o perfil.
        Verifica que os temas light e dark estão disponíveis.
        """
        self.assertEqual(
            Profile.THEME_CHOICES,
            [
                ("light", "Light"),
                ("dark", "Dark"),
            ],
        )

    def test_profile_default_theme(self):
        """
        Testa que o tema padrão do perfil é 'light'.
        Verifica o valor inicial do tema.
        """
        self.assertEqual(self.user.profile.theme, "light")  # type: ignore

    def test_profile_theme_update(self):
        """
        Testa a atualização do tema do perfil.
        Verifica que o tema pode ser alterado de light para dark.
        """
        self.user.profile.theme = "dark"  # type: ignore
        self.user.profile.save()  # type: ignore

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.theme, "dark")  # type: ignore


class SignalTests(TestCase):
    """
    Testa os sinais (signals) do Django.
    Verifica a criação automática de perfil e histórico de preços.
    """

    def test_profile_creation_signal(self):
        """
        Testa que o perfil é criado automaticamente quando um usuário é criado.
        Verifica que o sinal post_save funciona corretamente.
        """
        user = UserFactory.create()

        self.assertTrue(hasattr(user, "profile"))
        self.assertIsInstance(user.profile, Profile)  # type: ignore

    def test_price_history_signal_on_product_creation(self):
        """
        Testa que o histórico de preços é criado automaticamente quando um produto é criado.
        Verifica que o sinal cria a primeira entrada de histórico com o preço inicial.
        """
        product = ProductFactory.create(price=Decimal("199.99"))

        self.assertEqual(product.price_history.count(), 1)
        history = product.price_history.first()
        self.assertEqual(history.price, Decimal("199.99"))  # type: ignore

    def test_price_history_signal_on_price_change(self):
        """
        Testa que o histórico de preços é criado quando o preço de um produto é alterado.
        Verifica que uma nova entrada é adicionada ao histórico.
        """
        product = ProductFactory.create(price=Decimal("100.00"))

        # Change price
        product.price = Decimal("150.00")
        product.save()

        self.assertEqual(product.price_history.count(), 2)
        prices = [h.price for h in product.price_history.order_by("changed_at")]
        self.assertEqual(prices, [Decimal("100.00"), Decimal("150.00")])

    def test_price_history_signal_no_duplicate_on_same_price(self):
        """
        Testa que nenhuma entrada duplicada é criada quando o preço não é alterado.
        Verifica que salvar o produto sem mudar o preço não cria uma nova entrada.
        """
        product = ProductFactory.create(price=Decimal("100.00"))

        # Save without changing price
        product.name = "Updated name"
        product.save()

        self.assertEqual(product.price_history.count(), 1)  # Only initial entry
