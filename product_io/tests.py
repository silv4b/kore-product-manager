import csv
import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from partners.models import Supplier
from products.models import Category, Product
from products.tests.factories import ProductFactory, UserFactory

from .models import ExportLog, ImportLog


def _make_csv_bytes(rows):
    """Helper to create CSV bytes with header for test uploads."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "nome", "descricao", "preco", "preco_custo", "estoque",
        "estoque_minimo", "categorias", "fornecedor", "publico",
    ])
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return output.getvalue().encode("utf-8-sig")


class ProductExportViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_export_returns_csv(self):
        ProductFactory.create(user=self.user, name="Produto A", price=Decimal("50.00"))
        ProductFactory.create(user=self.user, name="Produto B", price=Decimal("100.00"))

        response = self.client.get(reverse("product_io:product_export"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8-sig")
        self.assertIn("attachment; filename", response["Content-Disposition"])

        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertIn("Produto A", lines[1])
        self.assertIn("Produto B", lines[2])

    def test_export_only_includes_user_products(self):
        other_user = UserFactory.create(username="other")
        ProductFactory.create(user=self.user, name="Meu Produto")
        ProductFactory.create(user=other_user, name="Outro Produto")

        response = self.client.get(reverse("product_io:product_export"))
        content = response.content.decode("utf-8-sig")

        self.assertIn("Meu Produto", content)
        self.assertNotIn("Outro Produto", content)

    def test_export_creates_export_log(self):
        ProductFactory.create(user=self.user, name="Log Test")

        self.client.get(reverse("product_io:product_export"))

        log = ExportLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.rows_exported, 1)
        self.assertEqual(log.status, "SUCCESS")

    def test_export_header_row(self):
        response = self.client.get(reverse("product_io:product_export"))
        content = response.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        expected = {
            "nome", "descricao", "preco", "preco_custo", "estoque",
            "estoque_minimo", "categorias", "fornecedor", "publico",
            "criado_em", "atualizado_em",
        }
        self.assertEqual(set(reader.fieldnames), expected)

    def test_export_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("product_io:product_export"))
        self.assertNotEqual(response.status_code, 200)


class ProductImportViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_admin()
        self.client.force_login(self.user)

    def test_get_import_page(self):
        response = self.client.get(reverse("product_io:product_import"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "product_io/product_import.html")

    def test_import_creates_products(self):
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["Produto Teste", "Descricao", "99,90", "50,00", "10", "3", "Eletronicos", "Fornecedor X", "sim"],
        ]))
        response = self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.filter(user=self.user).count(), 1)
        product = Product.objects.get(name="Produto Teste")
        self.assertEqual(product.price, Decimal("99.90"))
        self.assertEqual(product.cost_price, Decimal("50.00"))
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.min_stock_level, 3)
        self.assertTrue(product.is_public)

    def test_import_creates_categories_and_suppliers(self):
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["Produto Cat", "Desc", "10,00", "5,00", "1", "0", "CatA|CatB", "Fornecedor Novo", "nao"],
        ]))
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        # 4 default categories + 2 new = 6
        self.assertEqual(Category.objects.filter(user=self.user).count(), 6)
        self.assertEqual(Supplier.objects.filter(user=self.user).count(), 1)
        product = Product.objects.get(name="Produto Cat")
        self.assertEqual(product.categories.count(), 2)
        self.assertIsNotNone(product.supplier)

    def test_import_reuses_existing_supplier(self):
        Supplier.objects.create(user=self.user, name="Fornecedor Existente")
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["Produto", "Desc", "10,00", "5,00", "1", "0", "", "Fornecedor Existente", "nao"],
        ]))
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        self.assertEqual(Supplier.objects.filter(user=self.user).count(), 1)

    def test_import_handles_missing_columns(self):
        csv_file = SimpleUploadedFile("test.csv", b"nome,preco\nProd,10,00\n")
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        log = ImportLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "FAILED")
        self.assertIn("descricao", log.error_details.lower())

    def test_import_handles_invalid_data(self):
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["", "Desc", "invalido", "5,00", "abc", "0", "", "", "nao"],
        ]))
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        self.assertEqual(Product.objects.count(), 0)
        log = ImportLog.objects.last()
        self.assertEqual(log.status, "FAILED")
        self.assertGreater(log.rows_failed, 0)

    def test_import_creates_import_log(self):
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["Prod Log", "Desc", "25,00", "10,00", "5", "1", "", "", "sim"],
        ]))
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        log = ImportLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.rows_processed, 1)
        self.assertEqual(log.rows_failed, 0)
        self.assertEqual(log.status, "SUCCESS")

    def test_import_partial_failure(self):
        csv_file = SimpleUploadedFile("test.csv", _make_csv_bytes([
            ["Produto OK", "Desc", "10,00", "5,00", "1", "0", "", "", "nao"],
            ["", "Desc2", "20,00", "10,00", "2", "0", "", "", "nao"],
        ]))
        self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )

        self.assertEqual(Product.objects.count(), 1)
        log = ImportLog.objects.last()
        self.assertEqual(log.status, "PARTIAL")
        self.assertEqual(log.rows_processed, 1)
        self.assertEqual(log.rows_failed, 1)

    def test_import_requires_login(self):
        self.client.logout()
        csv_file = SimpleUploadedFile("test.csv", b"")
        response = self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )
        self.assertNotEqual(response.status_code, 200)

    def test_import_rejects_non_csv(self):
        csv_file = SimpleUploadedFile("data.txt", b"nome,preco\nProd,10.00\n")
        response = self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Formato inválido")

    def test_import_empty_file(self):
        csv_file = SimpleUploadedFile("empty.csv", b"nome,preco\n")
        response = self.client.post(
            reverse("product_io:product_import"),
            {"csv_file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        log = ImportLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "FAILED")
