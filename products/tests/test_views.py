from decimal import Decimal

from django.contrib.auth.models import User
from django.forms import ModelForm
from django.test import Client
from django.urls import reverse

from products.models import Category, Product
from products.tests.factories import (
    CategoryFactory,
    PriceHistoryFactory,
    ProductFactory,
    UserFactory,
)
from products.tests.test_utils import BaseTestCase


class ProductViewTest(BaseTestCase):
    """
    Testa as views de produto.
    Verifica criação, edição, exclusão, listagem e detalhes de produtos.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.other_user = UserFactory.create(username="otheruser")
        self.category = CategoryFactory.create(user=self.user)
        # self.client.login(username="admin", password="Adm@1adn!!!")
        self.client.force_login(self.user)

    def test_product_list_view_authenticated(self):
        """
        Testa a view de listagem de produtos para usuário autenticado.
        Verifica que apenas os produtos do usuário são mostrados.
        """
        ProductFactory.create(user=self.user, name="Product 1")
        ProductFactory.create(user=self.user, name="Product 2")
        ProductFactory.create(user=self.other_user, name="Other Product")

        response = self.client.get(reverse("product_list"))

        # Now with admin login, should work properly
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product 1")
        self.assertContains(response, "Product 2")
        self.assertNotContains(response, "Other Product")  # Other user's products
        self.assertContains(response, "Meus Produtos")

    def test_product_list_view_unauthenticated(self):
        """
        Testa que a view de listagem redireciona usuário não autenticado para login.
        """
        self.client.logout()
        response = self.client.get(reverse("product_list"))

        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_product_list_with_filters(self):
        """
        Testa a listagem de produtos com filtros de busca.
        Verifica que a busca por texto funciona corretamente.
        """
        ProductFactory.create(
            user=self.user,
            name="Laptop",
            price=Decimal("1000.00"),
            stock=5,
            is_public=True,
        )
        ProductFactory.create(
            user=self.user,
            name="Phone",
            price=Decimal("500.00"),
            stock=15,
            is_public=False,
        )

        # Test search filter - expecting redirect to login
        response = self.client.get(reverse("product_list"), {"q": "Laptop"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Phone")

    def test_product_list_with_sorting(self):
        """
        Testa a ordenação da lista de produtos.
        Verifica que os produtos são ordenados corretamente por nome.
        """
        # 1. Criar produtos em ordem aleatória
        ProductFactory.create(user=self.user, name="B Product")
        ProductFactory.create(user=self.user, name="A Product")
        ProductFactory.create(user=self.user, name="C Product")

        # 2. Fazer a requisição com parâmetros de ordenação (Usuário logado = 200 OK)
        url = reverse("product_list")
        response = self.client.get(url, {"sort": "name", "dir": "asc"})

        # 3. Verificações
        self.assertEqual(response.status_code, 200)

        # 4. Pegar a lista de produtos que a View enviou para o Template
        # Nota: Ajuste "products" para o nome da variável que você usa na View (ex: "object_list")
        products_in_context = list(response.context["products"])

        # 5. Extrair apenas os nomes para comparar a ordem
        names = [p.name for p in products_in_context]

        # 6. Validar se a ordem é a esperada (A -> B -> C)
        self.assertEqual(names, ["A Product", "B Product", "C Product"])

    def test_product_create_view_get(self):
        """Testa a renderização do formulário de criação de produtos"""
        # O usuário já está logado pelo setUp da classe
        response = self.client.get(reverse("product_create"))

        # 1. Verifica se a página carregou com sucesso
        self.assertEqual(response.status_code, 200)

        # 2. Verifica se o texto esperado está no HTML
        # Certifique-se de que o template contém exatamente "Add Product"
        self.assertContains(response, "Novo Produto")
        self.assertContains(
            response,
            "Preencha os detalhes abaixo para gerenciar seu produto no inventário.",
        )

        # 3. Verifica se o formulário no contexto é do tipo correto
        # É melhor verificar se é uma instância de ModelForm
        type(response.context["form"])
        self.assertIsInstance(response.context["form"], ModelForm)

    def test_product_create_view_post_valid(self):
        """Test product creation with valid data"""
        # 1. Dados do formulário
        form_data = {
            "name": "New Product",
            "description": "New description",
            "price": "99,99",
            "is_public": True,
            "categories": [
                self.category.pk
            ],  # Passando o ID da categoria criada no setUp
        }

        # 2. Executa o POST
        response = self.client.post(reverse("product_create"), data=form_data)

        # 3. Verifica o redirecionamento de SUCESSO
        self.assertRedirects(response, reverse("product_list"))

        # 4. Verifica se o objeto realmente existe no Banco de Dados
        product = Product.objects.get(name="New Product")

        # 5. Validações de integridade
        self.assertEqual(product.user, self.user)
        self.assertEqual(product.price, Decimal("99.99"))
        self.assertEqual(product.stock, 0)
        self.assertTrue(product.is_public)

        # Dica: Verifique se a categoria foi associada corretamente (se for ManyToMany)
        self.assertIn(self.category, product.categories.all())

    def test_product_create_view_post_invalid(self):
        """Test product creation with invalid data"""
        form_data = {
            "name": " ",  # Required field missing
            "price": "invalid",
        }

        response = self.client.post(reverse("product_create"), data=form_data)

        # 1. Quando o form é inválido, o Django retorna 200 (re-renderiza a página)
        self.assertEqual(response.status_code, 200)

        # 2. Verificamos se o formulário no contexto tem erros
        form = response.context["form"]
        self.assertFalse(form.is_valid())

        # Você pode verificar erros específicos em campos
        self.assertIn("name", form.errors)
        self.assertIn("price", form.errors)

        # 3. Garantimos que nenhum produto foi criado no banco de dados
        self.assertEqual(Product.objects.count(), 0)

    def test_product_update_view_get(self):
        """Test product update view GET request"""
        product = ProductFactory.create(user=self.user, name="Original Name")
        response = self.client.get(reverse("product_update", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, 200)
        # Verificamos se o formulário contém o nome original do produto
        self.assertContains(response, "Original Name")

        # Verificamos se o objeto no formulário é o produto correto
        from django.forms import ModelForm

        self.assertIsInstance(response.context["form"], ModelForm)
        self.assertEqual(response.context["form"].instance, product)

    def test_product_update_view_post_valid(self):
        """Test product update with valid data"""
        product = ProductFactory.create(user=self.user, name="Original Name", stock=20)

        form_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "price": "150,00",  # Changed from "150,00" to "150.00"
            "is_public": False,
        }
        # Realiza o POST
        response = self.client.post(
            reverse("product_update", kwargs={"pk": product.pk}), data=form_data
        )

        # Verifica o redirecionamento de SUCESSO, O Django redireciona para a lista após editar, não para o login
        self.assertRedirects(response, reverse("product_list"))

        # Recarrega o objeto do banco de dados para ver as mudanças
        product.refresh_from_db()

        # Valida se os dados foram realmente salvos
        self.assertEqual(product.name, "Updated Name")
        self.assertEqual(product.price, Decimal("150.00"))
        self.assertEqual(product.stock, 20)
        self.assertFalse(product.is_public)

    def test_product_update_view_permission_denied(self):
        """Test product update permission denied for other user's product"""
        product = ProductFactory.create(user=self.other_user)

        response = self.client.get(
            reverse("product_update", kwargs={"pk": product.pk}),
        )

        # Esperado um 404
        self.assertEqual(response.status_code, 404)

    def test_product_delete_view_get(self):
        """Test product delete confirmation view"""
        product = ProductFactory.create(user=self.user, name="To Delete")

        response = self.client.get(
            reverse("product_delete", kwargs={"pk": product.pk}),
        )

        # Ao remover um produto, deve ser redirecionado para a confirmação de remoção
        self.assertEqual(response.status_code, 200)

        # Verifica se estamos no template correto de confirmação
        self.assertTemplateUsed(response, "products/product_confirm_delete.html")
        self.assertContains(response, "To Delete")

    def test_product_delete_view_post(self):
        """Test product deletion"""
        product = ProductFactory.create(user=self.user, name="To Delete")

        response = self.client.post(
            reverse("product_delete", kwargs={"pk": product.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_product_detail_view_public(self):
        """Test viewing public product details"""
        product = ProductFactory.create(
            user=self.user, name="Public Product", is_public=True
        )

        response = self.client.get(reverse("product_detail", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Product")

    def test_product_detail_view_private_owner(self):
        """Test viewing own private product"""
        product = ProductFactory.create(
            user=self.user, name="Private Product", is_public=False
        )

        response = self.client.get(reverse("product_detail", kwargs={"pk": product.pk}))

        # Deve ser redirecionado para a página de detalhe de produto
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_detail_modal.html")
        self.assertContains(response, "Private Product")

    def test_product_detail_view_private_other_user(self):
        """Test viewing other user's private product"""
        product = ProductFactory.create(
            user=self.other_user, name="Private Product", is_public=False
        )

        response = self.client.get(reverse("product_detail", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_price_history_view(self):
        """Test price history view"""
        product = ProductFactory.create(user=self.user, is_public=True)

        PriceHistoryFactory.create(product=product, price=Decimal("100.00"))
        PriceHistoryFactory.create(product=product, price=Decimal("150.00"))
        PriceHistoryFactory.create(product=product, price=Decimal("130.00"))

        response = self.client.get(reverse("price_history", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100,00")
        self.assertContains(response, "150,00")
        self.assertContains(response, "130,00")

    def test_price_history_overview_view(self):
        """Test price history overview view"""
        product1 = ProductFactory.create(user=self.user)
        product2 = ProductFactory.create(user=self.user)

        PriceHistoryFactory.create(product=product1, price=Decimal("100.00"))
        PriceHistoryFactory.create(product=product2, price=Decimal("200.00"))

        response = self.client.get(reverse("price_history_overview"))

        self.assertEqual(response.status_code, 200)

        # 4 alterações, pois o primeiro valor é contabilizado como alteração.
        self.assertEqual(response.context["total_alteracoes"], 4)


class CategoryViewTest(BaseTestCase):
    """
    Testa as views de categoria.
    Verifica criação, edição, exclusão, listagem e duplicação de categorias.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.login(username="admin", password="Adm@1adn!!!")

    def test_category_list_view(self):
        """Test category list view"""
        CategoryFactory.create(user=self.user, name="Category A")
        CategoryFactory.create(user=self.user, name="Category B")

        response = self.client.get(reverse("category_list"))

        # Expecting redirect to login
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Category A")
        self.assertContains(response, "Category B")

    def test_category_list_view_sorting(self):
        """Test category list sorting"""
        CategoryFactory.create(user=self.user, name="Z Category")
        CategoryFactory.create(user=self.user, name="A Category")

        response = self.client.get(
            reverse("category_list"), {"sort": "name", "dir": "asc"}
        )
        categories = list(response.context["categories"])
        names = [c.name for c in categories]
        # "Eletronicos", "Importados", "Nacionais", "Utensilios" são as categorias base que todo novo usuário "Ganha"
        self.assertEqual(
            names,
            [
                "A Category",
                "Eletronicos",
                "Importados",
                "Nacionais",
                "Utensilios",
                "Z Category",
            ],
        )

    def test_category_create_view_get(self):
        """Test category creation view GET"""
        response = self.client.get(reverse("category_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nova Categoria")

    def test_category_create_view_post_valid(self):
        """Test category creation with valid data"""
        form_data = {
            "name": "New Category",
            "slug": "new-category",
            "description": "New description",
            "color": "#ff0000",
        }
        response = self.client.post(reverse("category_create"), data=form_data)

        self.assertEqual(response.status_code, 302)
        category = Category.objects.get(name="New Category")
        self.assertEqual(category.name, "New Category")
        self.assertEqual(category.slug, "new-category")

    def test_category_update_view(self):
        """Test category update view"""
        category = CategoryFactory.create(user=self.user, name="Original Name")

        form_data = {
            "name": "Updated Name",
            "slug": "updated-name",
            "description": "Updated description",
            "color": "#00ff00",
        }
        response = self.client.post(
            reverse("category_update", kwargs={"pk": category.pk}), data=form_data
        )

        self.assertEqual(response.status_code, 302)
        category.refresh_from_db()
        self.assertEqual(category.name, "Updated Name")

    def test_category_delete_view(self):
        """Test category deletion"""
        category = CategoryFactory.create(user=self.user, name="To Delete")

        response = self.client.post(
            reverse("category_delete", kwargs={"pk": category.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_category_duplicate_view(self):
        """Test category duplication"""
        original = CategoryFactory.create(
            user=self.user,
            name="Original",
            slug="original",
            description="Original desc",
            color="#ff0000",
        )

        response = self.client.get(
            reverse("category_duplicate", kwargs={"pk": original.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Original (Copy)")
        self.assertContains(response, "original-copy")


class PublicCatalogViewTest(BaseTestCase):
    """
    Testa as views do catálogo público de produtos.
    Verifica a visualização de produtos públicos por usuários autenticados e anônimos.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.other_user = UserFactory.create(username="cataloguser")
        self.category = CategoryFactory.create()

    def test_public_product_list_view(self):
        """Test public product list view"""
        ProductFactory.create(
            user=self.other_user, name="Public Product", is_public=True
        )
        ProductFactory.create(
            user=self.other_user, name="Private Product", is_public=False
        )
        ProductFactory.create(user=self.user, name="My Public Product", is_public=True)

        response = self.client.get(reverse("public_product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Product")
        self.assertContains(response, "My Public Product")
        self.assertNotContains(response, "Private Product")

    def test_user_public_catalog_view(self):
        """Test user-specific public catalog"""
        ProductFactory.create(
            user=self.other_user, name="Other Product", is_public=True
        )
        ProductFactory.create(user=self.user, name="My Product", is_public=True)

        response = self.client.get(
            reverse("user_public_catalog", kwargs={"username": "cataloguser"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Other Product")
        self.assertNotContains(response, "My Product")

    def test_user_public_catalog_not_found(self):
        """Test user catalog for non-existent user"""
        response = self.client.get(
            reverse("user_public_catalog", kwargs={"username": "nonexistent"})
        )

        self.assertEqual(response.status_code, 404)


class AccountViewTest(BaseTestCase):
    """
    Testa as views de conta de usuário.
    Verifica perfil, atualização e exclusão de conta.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.login(username="admin", password="Adm@1adn!!!")

    def test_profile_view_get(self):
        """Test profile view GET request"""
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.get_full_name())
        self.assertContains(response, self.user.get_username())
        # profile/ tem esse texto no html
        self.assertContains(response, "Informações Pessoais")

    def test_profile_view_post_valid(self):
        """Test profile update with valid data"""
        form_data = {"username": "newusername", "email": "newemail@example.com"}
        response = self.client.post(reverse("profile"), data=form_data)

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")
        self.assertEqual(self.user.email, "newemail@example.com")

    def test_delete_account_view_post_valid_password(self):
        """Test account deletion with correct password"""
        target_user = UserFactory.create(
            username="usuario_descartavel", password="senha_descartavel"
        )
        target_user.save()
        target_id = target_user.pk

        self.client.force_login(target_user)

        form_data = {"password": "senha_descartavel"}
        response = self.client.post(reverse("delete_account"), data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=target_id).exists())

    def test_delete_account_view_post_invalid_password(self):
        """Test account deletion with incorrect password"""
        form_data = {"password": "wrongpassword"}
        response = self.client.post(reverse("delete_account"), data=form_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())


class UtilityViewTest(BaseTestCase):
    """
    Testa as views utilitárias.
    Verifica alternância de tema, modo de visualização e logout.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.login(username="admin", password="Adm@1adn!!!")

    def test_toggle_theme_view(self):
        """Test theme toggle functionality"""
        # Initially light theme
        response = self.client.get(reverse("toggle_theme"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("theme"), "dark")

        # Toggle back to light
        response = self.client.get(reverse("toggle_theme"))
        self.assertEqual(self.client.session.get("theme"), "light")

    def test_set_view_mode_view(self):
        """Test view mode setting"""
        self.client.logout()

        url = reverse("set_view_mode", kwargs={"context": "test_ctx", "mode": "grid"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("view_mode_test_ctx"), "grid")

        url = reverse("set_view_mode", kwargs={"context": "test_ctx", "mode": "table"})
        response = self.client.get(url)
        self.assertEqual(self.client.session.get("view_mode_test_ctx"), "table")

    def test_set_view_mode_authenticated(self):
        """Test view mode setting for authenticated user"""
        url = reverse("set_view_mode", kwargs={"context": "prod_list", "mode": "table"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.user.profile.refresh_from_db()  # type: ignore
        self.assertEqual(self.user.profile.view_preferences.get("prod_list"), "table")  # type: ignore

    def test_logout_view_post(self):
        """Test custom logout view"""
        response = self.client.post(reverse("custom_logout"))
        self.assertEqual(response.status_code, 302)


class MessageTest(BaseTestCase):
    """
    Testa as mensagens de feedback (toast messages).
    Verifica que mensagens de sucesso e erro são exibidas corretamente.
    """

    def setUp(self):
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_success_messages(self):
        """Testa se a mensagem de Toast aparece com o formato correto"""
        product_name = "Produto Teste"

        response = self.client.post(
            reverse("product_create"),
            {
                "name": product_name,
                "price": "100.00",
            },
            follow=True,  # Essencial para capturar a mensagem após o redirecionamento
        )

        # from utils.general.rich_print import beautify_response
        # beautify_response(response)  # type: ignore # _MonkeyPatchedWSGIResponse herda de HttpResponse

        # A string exata que a sua View gera:

        # 1. Validação via Helper
        self.assertContains(response, "criado com sucesso!")

        # 2. Validação no HTML (garante que as aspas não foram "quebradas" pelo HTML escape)
        self.assertContains(response, "criado com sucesso!")

    def test_error_messages(self):
        """Testa se o acesso negado retorna 404 por segurança"""
        other_user = UserFactory.create(username="other")
        product = ProductFactory.create(user=other_user)

        # Como o usuário logado não é o dono, a View retorna 404 (pelo get_object_or_404)
        response = self.client.get(reverse("product_update", kwargs={"pk": product.pk}))

        self.assertEqual(response.status_code, 404)
