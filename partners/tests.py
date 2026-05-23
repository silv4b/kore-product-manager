from datetime import date

import pytest
from django.urls import reverse

from partners.forms import CustomerForm, SupplierForm
from partners.models import Customer, Supplier
from partners.templatetags.partner_masks import mask_cnpj, mask_cpf, mask_phone
from products.tests.factories import UserFactory


@pytest.fixture
def user(db):
    return UserFactory.create(username="partneruser", password="password123", email="partner@example.com")


@pytest.fixture
def other_user(db):
    return UserFactory.create(username="otherpartner", password="password123", email="otherpartner@example.com")


@pytest.fixture
def logged_client(client, user):
    client.login(username="partneruser", password="password123")
    return client


@pytest.fixture
def other_logged_client(client, other_user):
    client.login(username="otherpartner", password="password123")
    return client


@pytest.fixture
def customer(user):
    return Customer.objects.create(
        user=user,
        name="Bruno Silva",
        email="bruno@example.com",
        phone="11999999999",
        cpf="12345678909",
        birth_date=date(1990, 5, 20),
        street="Rua A",
        number="123"
    )


@pytest.fixture
def supplier(user):
    return Supplier.objects.create(
        user=user,
        name="LogTech Distribuidora",
        email="contato@logtech.com",
        phone="1133334444",
        cnpj="12345678000199",
        company_name="LogTech LTDA",
        contact_person="Carlos",
        website="https://logtech.com",
        street="Av. B",
        number="456"
    )


@pytest.mark.django_db
class TestPartnerModels:
    """
    Testa a criação e comportamento dos modelos Customer e Supplier.
    """

    def test_customer_creation(self, customer):
        assert str(customer) == "Cliente: Bruno Silva"
        assert customer.cpf == "12345678909"

    def test_supplier_creation(self, supplier):
        assert str(supplier) == "Fornecedor: LogTech Distribuidora"
        assert supplier.cnpj == "12345678000199"


@pytest.mark.django_db
class TestPartnerForms:
    """
    Testa os formulários de parceiros.
    """

    def test_customer_form_valid(self):
        data = {
            "name": "João Silva",
            "email": "joao@example.com",
            "phone": "11988887777",
            "cpf": "11122233344",
            "birth_date": "1995-10-12",
            "street": "Rua das Flores",
            "number": "4"
        }
        form = CustomerForm(data)
        assert form.is_valid()

    def test_customer_form_invalid_email(self):
        data = {
            "name": "João Silva",
            "email": "email-invalido",
        }
        form = CustomerForm(data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_supplier_form_valid(self):
        data = {
            "name": "Fornecedor X",
            "cnpj": "99888777000166",
            "email": "x@supplier.com",
            "website": "https://supplier.com"
        }
        form = SupplierForm(data)
        assert form.is_valid()

    def test_supplier_form_invalid_website(self):
        data = {
            "name": "Fornecedor X",
            "website": "site-sem-protocolo"
        }
        form = SupplierForm(data)
        assert not form.is_valid()
        assert "website" in form.errors


@pytest.mark.django_db
class TestPartnerViews:
    """
    Testa os fluxos das views (CRUD) de clientes e fornecedores.
    """

    def test_partner_list_requires_login(self, client):
        response = client.get(reverse("partner_list"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_partner_list_shows_only_user_data(self, logged_client, customer, supplier, other_user):
        # Cria dados para o outro usuário
        other_customer = Customer.objects.create(user=other_user, name="Invasor Cliente")
        other_supplier = Supplier.objects.create(user=other_user, name="Invasor Fornecedor")

        response = logged_client.get(reverse("partner_list"))
        assert response.status_code == 200

        # Deve exibir os dados do usuário autenticado na query do contexto
        assert customer in response.context["customers"]
        assert supplier in response.context["suppliers"]
        assert response.context["customers"].count() == 1
        assert response.context["suppliers"].count() == 1

        # Não deve conter dados do outro usuário no contexto
        assert other_customer not in response.context["customers"]
        assert other_supplier not in response.context["suppliers"]

    def test_customer_create_happy_path(self, logged_client):
        url = reverse("customer_create")
        data = {
            "name": "Ana Maria",
            "email": "ana@maria.com",
            "phone": "21988887777",
            "cpf": "98765432100",
            "birth_date": "1988-03-25",
            "street": "Rua C",
            "number": "99"
        }
        response = logged_client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("customer_list")

        # Verifica se foi salvo no banco e associado ao usuário
        assert Customer.objects.filter(name="Ana Maria", user__username="partneruser").exists()

    def test_customer_update_happy_path(self, logged_client, customer):
        url = reverse("customer_update", kwargs={"pk": customer.id})
        data = {
            "name": "Bruno Silva Editado",
            "email": "bruno.editado@example.com",
        }
        response = logged_client.post(url, data)
        assert response.status_code == 302

        customer.refresh_from_db()
        assert customer.name == "Bruno Silva Editado"

    def test_customer_update_other_user_data_returns_404(self, other_logged_client, customer):
        url = reverse("customer_update", kwargs={"pk": customer.id})
        response = other_logged_client.get(url)
        assert response.status_code == 404

        response = other_logged_client.post(url, {"name": "Invasão"})
        assert response.status_code == 404

    def test_customer_delete_happy_path(self, logged_client, customer):
        url = reverse("customer_delete", kwargs={"pk": customer.id})

        # GET retorna confirmação
        response = logged_client.get(url)
        assert response.status_code == 200
        assert "partners/partner_confirm_delete.html" in [t.name for t in response.templates]

        # POST deleta
        response = logged_client.post(url)
        assert response.status_code == 302
        assert not Customer.objects.filter(id=customer.id).exists()

    def test_customer_delete_other_user_data_returns_404(self, other_logged_client, customer):
        url = reverse("customer_delete", kwargs={"pk": customer.id})
        response = other_logged_client.post(url)
        assert response.status_code == 404
        assert Customer.objects.filter(id=customer.id).exists()

    def test_supplier_create_happy_path(self, logged_client):
        url = reverse("partner_supplier_create")
        data = {
            "name": "Fornecedor Z",
            "cnpj": "99988877000155",
            "email": "z@forn.com"
        }
        response = logged_client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("partner_supplier_list")
        assert Supplier.objects.filter(name="Fornecedor Z").exists()

    def test_supplier_update_happy_path(self, logged_client, supplier):
        url = reverse("partner_supplier_update", kwargs={"pk": supplier.id})
        data = {
            "name": "Fornecedor Editado",
            "cnpj": "12345678000199",
            "email": "editado@logtech.com"
        }
        response = logged_client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("partner_supplier_list")
        supplier.refresh_from_db()
        assert supplier.name == "Fornecedor Editado"

    def test_supplier_update_other_user_data_returns_404(self, other_logged_client, supplier):
        url = reverse("partner_supplier_update", kwargs={"pk": supplier.id})
        response = other_logged_client.get(url)
        assert response.status_code == 404

    def test_supplier_delete_happy_path(self, logged_client, supplier):
        url = reverse("partner_supplier_delete", kwargs={"pk": supplier.id})

        response = logged_client.get(url)
        assert response.status_code == 200
        assert "partners/partner_confirm_delete.html" in [t.name for t in response.templates]

        response = logged_client.post(url)
        assert response.status_code == 302
        assert response.url == reverse("partner_supplier_list")
        assert not Supplier.objects.filter(id=supplier.id).exists()

    def test_supplier_delete_other_user_data_returns_404(self, other_logged_client, supplier):
        url = reverse("partner_supplier_delete", kwargs={"pk": supplier.id})
        response = other_logged_client.post(url)
        assert response.status_code == 404
        assert Supplier.objects.filter(id=supplier.id).exists()


def test_partner_masks():
    """
    Testa as funções de máscara do templatetag partner_masks.
    """
    # Testes CPF
    assert mask_cpf("12345678909") == "123.456.789-09"
    assert mask_cpf("123.456.789-09") == "123.456.789-09"
    assert mask_cpf("") == "-"
    assert mask_cpf(None) == "-"
    assert mask_cpf("123") == "123"

    # Testes CNPJ
    assert mask_cnpj("12345678000199") == "12.345.678/0001-99"
    assert mask_cnpj("") == "-"
    assert mask_cnpj("12345") == "12345"

    # Testes Telefone
    assert mask_phone("11999998888") == "(11) 99999-8888" # Celular (11 dígitos)
    assert mask_phone("1133334444") == "(11) 3333-4444"   # Fixo (10 dígitos)
    assert mask_phone("") == "-"
    assert mask_phone("123") == "123"
