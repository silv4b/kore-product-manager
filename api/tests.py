import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

from products.models import Category, Product


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser", password="password123", email="test@example.html"
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username="otheruser", password="password123", email="other@example.html"
    )


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
def category(user):
    return Category.objects.create(user=user, name="Hardware", slug="hardware")


@pytest.fixture
def product(user, category):
    p = Product.objects.create(user=user, name="Teclado", price=150.00, stock=10)
    p.categories.add(category)
    return p


@pytest.mark.django_db
class TestAuthentication:
    """
    Testa a autenticação via API usando tokens JWT.
    """

    def test_obtain_token(self, api_client, user):
        """
        Testa a obtenção de tokens JWT (access e refresh).
        Verifica que um usuário válido pode obter tokens de autenticação.
        """


@pytest.mark.django_db
class TestCategoryAPI:
    """
    Testa endpoints da API REST para gerenciamento de categorias.
    """

    def test_list_categories(self, auth_client, category):
        """
        Testa a listagem de categorias via API.
        Verifica que as categorias do usuário são retornadas corretamente.
        """

    def test_create_category(self, auth_client):
        """
        Testa a criação de uma nova categoria via API.
        Verifica que a categoria é criada corretamente no banco de dados.
        """


@pytest.mark.django_db
class TestProductAPI:
    """
    Testa endpoints da API REST para gerenciamento de produtos.
    """

    def test_list_products(self, auth_client, product):
        """
        Testa a listagem de produtos via API.
        Verifica que os produtos do usuário são retornados corretamente.
        """

    def test_create_product(self, auth_client, category):
        """
        Testa a criação de um novo produto via API.
        Verifica que o produto é criado com as categorias associadas.
        """

    def test_product_detail(self, auth_client, product):
        """
        Testa a visualização dos detalhes de um produto via API.
        Verifica que o histórico de preços e movimentos são retornados.
        """

    def test_other_user_cannot_access_product(self, api_client, other_user, product):
        """
        Testa que um usuário não pode acessar produtos de outro usuário.
        Verifica que o acesso é negado com erro 404.
        """


@pytest.mark.django_db
class TestMovementAPI:
    """
    Testa endpoints da API REST para gerenciamento de movimentos de estoque.
    """

    def test_perform_in_movement(self, auth_client, product):
        """
        Testa a realização de um movimento de entrada (IN) de estoque.
        Verifica que o estoque do produto é aumentado corretamente.
        """

    def test_perform_out_movement_insufficient_stock(self, auth_client, product):
        """
        Testa que não é possível realizar um movimento de saída (OUT)
        quando o estoque é insuficiente.
        """
