from datetime import timedelta
from decimal import Decimal

from django.test import Client
from django.urls import reverse
from django.utils import timezone

from products.models import Category, Product
from products.tests.factories import CategoryFactory, ProductFactory, UserFactory
from products.tests.test_utils import BaseTestCase


class ProductWorkflowTest(BaseTestCase):
    """
    Testa fluxos de trabalho completos do usuário para gerenciamento de produtos.
    Inclui testes de ciclo de vida, filtragem e catálogo público.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        # Force login - não precisa de senha!
        self.client.force_login(self.user)

    def test_complete_product_lifecycle(self):
        """
        Testa o ciclo de vida completo de um produto desde a criação até a exclusão.
        Inclui: criação, listagem,visualização de detalhes, atualização,
        histórico de preços e exclusão do produto.
        """
        category = CategoryFactory.create(name="Test Category", user=self.user)

        # Criando o produto
        create_data = {
            "name": "Notebook Lenovo Thinkpad",
            "description": "Notebook Top das Galáxias",
            "price": "5299,99",
            "stock": 5,
            "is_public": True,
            "categories": [category.pk],
        }

        response = self.client.post(reverse("product_create"), data=create_data)

        # from utils.general.rich_print import beautify_response
        # beautify_response(response=response)

        self.assertEqual(response.status_code, 302)

        product = Product.objects.get(name="Notebook Lenovo Thinkpad")
        self.assertEqual(product.user, self.user)
        self.assertEqual(product.price, Decimal("5299.99"))
        self.assertIn(category, product.categories.all())

        # Verify price history was created
        self.assertEqual(product.price_history.count(), 1)

        # 2. View product list
        response = self.client.get(reverse("product_list"))
        self.assertContains(response, "Notebook Lenovo Thinkpad")

        # 3. View product details
        response = self.client.get(reverse("product_detail", kwargs={"pk": product.pk}))
        self.assertContains(response, "Notebook Lenovo Thinkpad")
        self.assertContains(response, "Notebook Top das Galáxias")

        # 4. Update product
        update_data = {
            "name": "Updated Laptop",
            "description": "Updated description",
            "price": "9999,99",
            "stock": 3,
            "is_public": False,
        }

        response = self.client.post(
            reverse("product_update", kwargs={"pk": product.pk}), data=update_data
        )
        self.assertEqual(response.status_code, 302)

        product.refresh_from_db()

        self.assertEqual(product.name, "Updated Laptop")
        self.assertEqual(product.price, Decimal("9999.99"))
        self.assertFalse(product.is_public)

        # Verify price history was updated
        self.assertEqual(product.price_history.count(), 2)

        # 5. View price history
        response = self.client.get(reverse("price_history", kwargs={"pk": product.pk}))
        self.assertContains(response, "5.299,99")
        self.assertContains(response, "999,99")

        # 6. Delete product
        response = self.client.post(
            reverse("product_delete", kwargs={"pk": product.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_product_filtering_workflow(self):
        """
        Testa o fluxo de filtragem e ordenação de produtos com múltiplos critérios.
        Inclui: busca por texto, filtro por categoria, faixa de preço,
        estoque mínimo e ordenação por preço.
        """

        category_electronics = CategoryFactory.create(name="Electronics")
        category_books = CategoryFactory.create(name="Books")

        # Criamos os produtos e capturamos as instâncias retornadas
        laptop = ProductFactory.create(
            user=self.user,
            name="Laptop",
            price=Decimal("1000.00"),
            stock=5,
            is_public=True,
        )
        phone = ProductFactory.create(
            user=self.user,
            name="Phone",
            price=Decimal("500.00"),
            stock=10,
            is_public=False,
        )
        book = ProductFactory.create(
            user=self.user,
            name="Book",
            price=Decimal("20.00"),
            stock=50,
            is_public=True,
        )

        # Atribuindo categorias
        laptop.categories.add(category_electronics)
        phone.categories.add(category_electronics)
        book.categories.add(category_books)

        # 1. Teste de busca por texto (parâmetro 'q')
        response = self.client.get(reverse("product_list"), {"q": "Book"})
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], book)

        self.client.get(reverse("product_list") + "?clear=1")

        # 2. Teste de filtro por categoria
        response = self.client.get(
            reverse("product_list"), {"category": category_electronics.pk, "q": ""}
        )
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual(len(products), 2)

        # Verificando se os itens corretos estão presentes e o incorreto está ausente
        product_ids = [p.pk for p in products]
        self.assertIn(laptop.pk, product_ids)
        self.assertIn(phone.pk, product_ids)
        self.assertNotIn(book.pk, product_ids)

        self.client.get(reverse("product_list") + "?clear=1")

        # 3. Teste de faixa de preço (min_price e max_price)
        response = self.client.get(
            reverse("product_list"), {"min_price": "200", "max_price": "800"}
        )
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], phone)

        self.client.get(reverse("product_list") + "?clear=1")

        # 4. Teste de estoque mínimo (min_stock)
        response = self.client.get(reverse("product_list"), {"min_stock": "20"})
        products = response.context["products"]
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], book)

        self.client.get(reverse("product_list") + "?clear=1")

        # 5. Teste de ordenação por preço ascendente
        response = self.client.get(
            reverse("product_list"), {"sort": "price", "dir": "asc"}
        )
        self.assertEqual(response.status_code, 200)

        # Extraindo apenas os preços para validar a ordem numérica
        prices = [p.price for p in response.context["products"]]
        expected_prices = [Decimal("20.00"), Decimal("500.00"), Decimal("1000.00")]
        self.assertEqual(prices, expected_prices)

    def test_public_catalog_workflow(self):
        """
        Testa o fluxo de visualização do catálogo público de produtos.
        Verifica que produtos públicos são visíveis e privados não são expostos.
        """
        other_user = UserFactory.create(username="seller")
        category = CategoryFactory.create(name="Gadgets")

        # Create products for other user
        public_product = ProductFactory.create(
            user=other_user,
            name="Public Gadget",
            price=Decimal("100.00"),
            is_public=True,
        )
        public_product.categories.add(category)

        ProductFactory.create(
            user=other_user,
            name="Private Gadget",
            price=Decimal("200.00"),
            is_public=False,
        )

        # Create own products
        ProductFactory.create(
            user=self.user, name="My Product", price=Decimal("150.00"), is_public=True
        )

        # Test public catalog view
        response = self.client.get(reverse("public_product_list"))
        self.assertContains(response, "Public Gadget")
        self.assertContains(response, "My Product")
        self.assertNotContains(response, "Private Gadget")

        # Test user-specific catalog
        response = self.client.get(
            reverse("user_public_catalog", kwargs={"username": "seller"})
        )
        self.assertContains(response, "Public Gadget")
        self.assertNotContains(response, "My Product")
        self.assertNotContains(response, "Private Gadget")

        # Test category filtering in public catalog
        response = self.client.get(
            reverse("user_public_catalog", kwargs={"username": "seller"}),
            {"category": category.pk},
        )
        self.assertContains(response, "Public Gadget")


class CategoryWorkflowTest(BaseTestCase):
    """
    Testa fluxos de trabalho completos do usuário para gerenciamento de categorias.
    Inclui testes de ciclo de vida completo das categorias.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_complete_category_lifecycle(self):
        """
        Testa o ciclo de vida completo de uma categoria desde a criação até a exclusão.
        Inclui: criação, listagem, atualização, duplicação e exclusão da categoria.
        """
        # Cria a categoria
        create_data = {
            "name": "New Category",
            "slug": "new-category",
            "description": "Category description",
            "color": "#ff5733",
        }

        response = self.client.post(reverse("category_create"), data=create_data)
        self.assertEqual(response.status_code, 302)

        category = Category.objects.get(name="New Category")
        self.assertEqual(category.slug, "new-category")
        self.assertEqual(category.description, "Category description")
        self.assertEqual(category.color, "#ff5733")

        # Ver lista de categorias
        response = self.client.get(reverse("category_list"))
        self.assertContains(response, "New Category")

        # Atualizar a categoria
        update_data = {
            "name": "Updated Category",
            "slug": "updated-category",
            "description": "Updated description",
            "color": "#33ff57",
        }

        response = self.client.post(
            reverse("category_update", kwargs={"pk": category.pk}), data=update_data
        )
        self.assertEqual(response.status_code, 302)

        category.refresh_from_db()
        self.assertEqual(category.name, "Updated Category")
        self.assertEqual(category.description, "Updated description")
        self.assertEqual(category.color, "#33ff57")

        # Duplicando a categoria
        response = self.client.get(
            reverse("category_duplicate", kwargs={"pk": category.pk})
        )

        # from utils.general.rich_print import beautify_response
        # beautify_response(response=response)

        self.assertContains(response, "Updated Category (Copy)")
        self.assertContains(response, "updated-category-copy")

        # Duplicação terminada
        response = self.client.post(
            reverse("category_duplicate", kwargs={"pk": category.pk}),
            {
                "name": "Updated Category (Copy)",
                "slug": "updated-category-copy",
                "description": "Updated description",
                "color": "#33ff57",
            },
        )
        self.assertEqual(response.status_code, 302)

        duplicated_category = Category.objects.get(name="Updated Category (Copy)")
        self.assertEqual(duplicated_category.slug, "updated-category-copy")

        # Deleta categoria original
        response = self.client.post(
            reverse("category_delete", kwargs={"pk": category.pk})
        )
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        self.assertTrue(Category.objects.filter(pk=duplicated_category.pk).exists())


class UserAccountWorkflowTest(BaseTestCase):
    """
    Testa fluxos de trabalho de gerenciamento de conta do usuário.
    Inclui registro, perfil, tema e preferências de visualização.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_complete_user_registration_and_profile_workflow(self):
        """
        Testa o fluxo de registro de usuário e gerenciamento de perfil.
        Inclui: atualização de perfil (nome de usuário/email), alternância de tema
        e configuração de modo de visualização.
        """
        # 1. Login
        self.client.login(username=self.user.username, password="testpass123")

        # --- 1. Update profile (Username/Email) ---
        profile_data = {"username": "newusername", "email": "newemail@example.com"}
        response = self.client.post(reverse("profile"), data=profile_data)
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")

        # --- 2. Test theme functionality ---
        response = self.client.get(reverse("toggle_theme"))
        self.assertEqual(response.status_code, 302)

        # Verifica no Perfil (Fonte da Verdade)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.theme, "dark")  # type: ignore

        # --- 3. Test view mode functionality ---
        context_name = "product_list"
        # Mudamos o modo para 'grid'
        response = self.client.get(
            reverse("set_view_mode", kwargs={"context": context_name, "mode": "grid"})
        )
        self.assertEqual(response.status_code, 302)

        # A. Verificação no Banco de Dados (Isso prova que a View rodou com sucesso)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.view_preferences.get(context_name), "grid")  # type: ignore

        # B. Verificação Real de Integração (O teste definitivo)
        # Em vez de brigar com o objeto 'session', vamos carregar a página de produtos
        # e ver se ela está usando o modo que acabamos de definir.
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

        # No seu views.py, a product_list pega o view_mode do perfil/sessão e joga no context
        self.assertEqual(response.context["view_mode"], "grid")


class PriceHistoryWorkflowTest(BaseTestCase):
    """
    Testa fluxos de trabalho de rastreamento de histórico de preços.
    Verifica a criação automática de registros de histórico quando preços mudam.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_price_history_tracking_workflow(self):
        """
        Testa o rastreamento automático do histórico de preços.
        Verifica que o histórico é criado quando um produto é criado e quando
        o preço é atualizado, incluindo filtragem por data.
        """
        # Create product
        product = ProductFactory.create(user=self.user, price=Decimal("100.00"))

        # Verify initial price history
        self.assertEqual(product.price_history.count(), 1)
        initial_history = product.price_history.first()

        # Asserção de que initial_history não é None.
        assert initial_history is not None
        self.assertEqual(initial_history.price, Decimal("100.00"))

        # Update price multiple times
        prices = [
            Decimal("120.00"),
            Decimal("95.00"),
            Decimal("110.00"),
            Decimal("110.00"),
            Decimal("135.00"),
        ]

        for price in prices:
            product.price = price
            product.save()

        # Verifica o histórico de preços, deve haver 5 entradas, sem duplicadas para 110 2x seguidas.
        self.assertEqual(product.price_history.count(), 5)

        # Verifica a view de histórico de preços.
        response = self.client.get(reverse("price_history", kwargs={"pk": product.pk}))
        self.assertEqual(response.status_code, 200)

        # Verifica a página de histórico de preço (com todos os produtos)
        response = self.client.get(reverse("price_history_overview"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "135,00"
        )  # Ultimo valor atualizado do produto em questão.

        # Testa o filtro de data no histórico de preço
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        response = self.client.get(
            reverse("price_history", kwargs={"pk": product.pk}),
            {
                "data_inicio": yesterday.strftime("%Y-%m-%d"),
                "data_fim": today.strftime("%Y-%m-%d"),
            },
        )

        self.assertEqual(response.status_code, 200)


class ErrorHandlingWorkflowTest(BaseTestCase):
    """
    Testa o tratamento de erros em vários fluxos de trabalho.
    Inclui cenários de permissão negada, validação de formulários e erros 404.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.other_user = UserFactory.create(username="otheruser")
        self.client.force_login(self.user)

    def test_permission_denied_workflow(self):
        """
        Testa cenários onde o acesso deve ser negado ou protegido.
        Verifica que usuários não podem acessar, editar ou excluir produtos privados de outros usuários.
        """
        # Cria um produto que NÃO pertence ao usuário logado
        private_product = ProductFactory.create(
            user=self.other_user, name="Private Item", is_public=False
        )

        # 2. Tentar acessar detalhes de um produto privado de outro usuário
        response = self.client.get(
            reverse("product_detail", kwargs={"pk": private_product.pk})
        )

        self.assertEqual(response.status_code, 302)

        # 3. Tentar editar produto de outro usuário
        # Na view product_detail usa get_object_or_404(Product, pk=pk, user=request.user)
        # Como o usuário logado não é o dono, DEVE retornar 404
        response = self.client.get(
            reverse("product_update", kwargs={"pk": private_product.pk})
        )
        self.assertEqual(response.status_code, 404)

        # 4. Tentar deletar produto de outro usuário
        # Mesmo comportamento: 404 por causa do filtro de usuário na QuerySet
        response = self.client.post(
            reverse("product_delete", kwargs={"pk": private_product.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_form_validation_workflow(self):
        """
        Testa erros de validação de formulários para produtos e categorias.
        Verifica que dados inválidos retornam erros apropriados.
        """

        # Teste de criação de produto inválido
        # Dados que violam as regras do Model/Form
        response = self.client.post(
            reverse("product_create"),
            {
                "name": "",  # Erro: Campo obrigatório
                "price": "not_a_num",  # Erro: Formato inválido
                "stock": -5,  # Erro: Valor negativo (se houver validação)
            },
        )

        # A página recarrega mostrando os erros
        self.assertEqual(response.status_code, 200)

        # Verifica se o formulário no contexto realmente contém erros
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("price", form.errors)
        self.assertIn("stock", form.errors)

        # Teste de criação de categoria inválida (Slug duplicado)
        CategoryFactory.create(slug="test-slug", user=self.user)

        response = self.client.post(
            reverse("category_create"),
            {
                "name": "Another Category",
                "slug": "test-slug",  # Slug duplicado para o mesmo user
                "color": "#ff0000",
            },
        )

        self.assertEqual(response.status_code, 200)

        form_cat = response.context["form"]
        self.assertFalse(form_cat.is_valid())
        self.assertIn("slug", form_cat.errors)
        self.assertEqual(
            form_cat.errors["slug"], ["Você já possui uma categoria com este slug."]
        )

    def test_not_found_workflow(self):
        """
        Testa cenários de erro 404 (página não encontrada).
        Verifica que produtos, categorias e usuários inexistentes retornam 404.
        """
        # Non-existent product
        response = self.client.get(reverse("product_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

        # Non-existent category
        response = self.client.get(reverse("category_update", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)

        # Non-existent user catalog
        response = self.client.get(
            reverse("user_public_catalog", kwargs={"username": "nonexistentuser"})
        )
        self.assertEqual(response.status_code, 404)
