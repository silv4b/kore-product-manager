from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from partners.models import Supplier
from products.models import Category, Product, ProductMovement
from products.tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory.create(username="testuser", password="password123", email="test@example.com")


@pytest.fixture
def other_user(db):
    return UserFactory.create(username="otheruser", password="password123", email="other@example.com")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": "testuser", "password": "password123"},
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def other_auth_client(api_client, other_user):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": "otheruser", "password": "password123"},
    )
    token = response.data["access"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def category(user):
    return Category.objects.create(user=user, name="Hardware", slug="hardware")


@pytest.fixture
def supplier(user):
    return Supplier.objects.create(user=user, name="Intel", email="intel@example.com")


@pytest.fixture
def product(user, category, supplier):
    p = Product.objects.create(
        user=user,
        name="Teclado",
        price=Decimal("150.00"),
        cost_price=Decimal("100.00"),
        stock=10,
        supplier=supplier
    )
    p.categories.add(category)
    return p


@pytest.mark.django_db
class TestAuthentication:
    """
    Testa a autenticação via API usando tokens JWT e validações de erro.
    """

    def test_obtain_token(self, api_client, user):
        """
        Testa a obtenção de tokens JWT válidos.
        """
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "password123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_invalid_password(self, api_client, user):
        """
        Testa a obtenção de tokens JWT com senha incorreta.
        """
        response = api_client.post(
            reverse("token_obtain_pair"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "access" not in response.data

    def test_request_without_auth_header(self, api_client):
        """
        Testa requisição em endpoint protegido sem cabeçalho de autorização.
        """
        response = api_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_with_invalid_token(self, api_client):
        """
        Testa requisição em endpoint protegido com token inválido.
        """
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalidtokenvalue")
        response = api_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCategoryAPI:
    """
    Testa endpoints da API REST para gerenciamento de categorias.
    """

    def test_list_categories(self, auth_client, category, other_user):
        """
        Testa a listagem de categorias via API.
        Verifica se retorna apenas as categorias pertencentes ao usuário autenticado.
        """
        other_cat = Category.objects.create(user=other_user, name="Outro", slug="outro")

        response = auth_client.get(reverse("category-list"))
        assert response.status_code == status.HTTP_200_OK

        ids = [cat["id"] for cat in response.data]
        assert category.id in ids
        assert other_cat.id not in ids

    def test_create_category(self, auth_client):
        """
        Testa a criação de uma nova categoria.
        """
        data = {"name": "Software", "slug": "software", "color": "#00ff00"}
        response = auth_client.post(reverse("category-list"), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Software"
        assert Category.objects.filter(name="Software", slug="software").exists()

    def test_create_category_validation_error(self, auth_client):
        """
        Testa erro de validação ao criar categoria sem campos obrigatórios.
        """
        data = {"slug": "sem-nome"}
        response = auth_client.post(reverse("category-list"), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_other_user_cannot_access_category(self, other_auth_client, category):
        """
        Garante que um usuário diferente não consegue obter/modificar a categoria.
        """
        url = reverse("category-detail", kwargs={"pk": category.id})

        response = other_auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = other_auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSupplierAPI:
    """
    Testa endpoints da API REST para gerenciamento de fornecedores.
    """

    def test_list_suppliers(self, auth_client, supplier, other_user):
        """
        Testa a listagem de fornecedores e garante o isolamento entre usuários.
        """
        other_supplier = Supplier.objects.create(user=other_user, name="AMD")
        response = auth_client.get(reverse("supplier-list"))
        assert response.status_code == status.HTTP_200_OK

        ids = [sup["id"] for sup in response.data]
        assert supplier.id in ids
        assert other_supplier.id not in ids

    def test_create_supplier(self, auth_client):
        """
        Testa a criação de um fornecedor.
        """
        data = {"name": "Dell", "email": "dell@dell.com", "observations": "Fornecedor de computadores"}
        response = auth_client.post(reverse("supplier-list"), data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Dell"

    def test_create_supplier_invalid(self, auth_client):
        """
        Testa validação de erro na criação (sem nome).
        """
        response = auth_client.post(reverse("supplier-list"), {"contact": "no-name"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data


@pytest.mark.django_db
class TestProductAPI:
    """
    Testa endpoints da API REST para gerenciamento de produtos.
    """

    def test_list_products(self, auth_client, product, other_user):
        """
        Testa listagem de produtos. Verifica se isola por usuário.
        """
        other_prod = Product.objects.create(user=other_user, name="Mouse AMD", price=50.00, stock=5)
        response = auth_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_200_OK

        ids = [prod["id"] for prod in response.data]
        assert product.id in ids
        assert other_prod.id not in ids

    def test_create_product(self, auth_client, category, supplier):
        """
        Testa a criação de um novo produto com categoria e fornecedor.
        """
        data = {
            "name": "Mouse Gamer",
            "description": "Mouse RGB",
            "price": "80.00",
            "cost_price": "40.00",
            "min_stock_level": 5,
            "stock": 15,
            "is_public": False,
            "category_ids": [category.id],
            "supplier_id": supplier.id,
        }
        response = auth_client.post(reverse("product-list"), data)
        print("DEBUG CREATE PRODUCT RESPONSE:", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Mouse Gamer"
        assert Decimal(response.data["profit_margin"]) == Decimal("100.00")

        p = Product.objects.get(name="Mouse Gamer")
        assert p.supplier == supplier
        assert category in p.categories.all()

    def test_create_product_validation_errors(self, auth_client):
        """
        Testa validações de dados inválidos ao criar produto.
        """
        data = {"price": "50.00", "stock": 10}
        response = auth_client.post(reverse("product-list"), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

        data = {"name": "Teclado", "price": "texto", "stock": 10}
        response = auth_client.post(reverse("product-list"), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_product_other_user_category_and_supplier(self, auth_client, other_user):
        """
        Garante que tentar associar categorias ou fornecedores de outros usuários causa erro de validação.
        """
        other_cat = Category.objects.create(user=other_user, name="Outro", slug="outro")
        other_sup = Supplier.objects.create(user=other_user, name="Outro Fornecedor")

        data = {
            "name": "Produto Invasor",
            "price": "10.00",
            "category_ids": [other_cat.id],
            "supplier_id": other_sup.id,
        }
        response = auth_client.post(reverse("product-list"), data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category_ids" in response.data or "supplier_id" in response.data

    def test_product_detail(self, auth_client, product):
        """
        Verifica a listagem de detalhes de um produto e se aninha o histórico de preços e movimentos.
        """
        ProductMovement.objects.create(product=product, type="IN", quantity=5, reason="Ajuste")

        url = reverse("product-detail", kwargs={"pk": product.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "price_history" in response.data
        assert "movements" in response.data
        assert len(response.data["movements"]) == 2

    def test_other_user_cannot_access_product(self, other_auth_client, product):
        """
        Garante que um usuário diferente não consegue visualizar nem modificar produtos de terceiros.
        """
        url = reverse("product-detail", kwargs={"pk": product.id})

        response = other_auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response = other_auth_client.put(url, {"name": "Novo Nome", "price": "20.00"})
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMovementAPI:
    """
    Testa endpoints da API REST para gerenciamento de movimentos de estoque.
    """

    def test_perform_in_movement(self, auth_client, product):
        """
        Testa a realização de um movimento de entrada (IN) de estoque.
        Verifica se o estoque é atualizado corretamente.
        """
        url = reverse("product-movement", kwargs={"pk": product.id})
        data = {"type": "IN", "quantity": 5, "reason": "Compra de lote"}

        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["quantity"] == 5

        product.refresh_from_db()
        assert product.stock == 15

    def test_perform_out_movement_insufficient_stock(self, auth_client, product):
        """
        Garante que saídas que ultrapassam o estoque disponível retornam erro 400.
        E que o estoque não seja modificado no banco de dados.
        """
        url = reverse("product-movement", kwargs={"pk": product.id})
        data = {"type": "OUT", "quantity": 11, "reason": "Venda"}

        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

        product.refresh_from_db()
        assert product.stock == 10

    def test_perform_out_movement_happy_path(self, auth_client, product):
        """
        Testa saída de estoque com saldo suficiente.
        """
        url = reverse("product-movement", kwargs={"pk": product.id})
        data = {"type": "OUT", "quantity": 4, "reason": "Venda"}

        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        product.refresh_from_db()
        assert product.stock == 6

    def test_perform_movement_invalid_quantity(self, auth_client, product):
        """
        Testa erro de validação ao enviar quantidade negativa ou zero.
        """
        url = reverse("product-movement", kwargs={"pk": product.id})

        response = auth_client.post(url, {"type": "IN", "quantity": -3})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = auth_client.post(url, {"type": "IN", "quantity": 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_movements_isolation(self, auth_client, other_auth_client, product, other_user):
        """
        Testa listagem de movimentos e isolamento de dados.
        """
        ProductMovement.objects.create(product=product, type="IN", quantity=2, reason="Ajuste")

        other_prod = Product.objects.create(user=other_user, name="Outro", price=10.00, stock=5)
        other_mov = ProductMovement.objects.create(product=other_prod, type="IN", quantity=4, reason="Outro ajuste")

        response = auth_client.get(reverse("movement-list"))
        assert response.status_code == status.HTTP_200_OK
        ids = [mov["id"] for mov in response.data]
        assert len(ids) == 1
        assert other_mov.id not in ids
