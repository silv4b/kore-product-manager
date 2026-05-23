import csv
import io

from django.db import transaction
from django.db.models import IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from partners.models import Supplier
from product_io.models import ExportLog, ImportLog
from products.models import Category, Product, ProductMovement, Stock, StorageLocation

from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductImportSerializer,
    ProductMovementSerializer,
    ProductSerializer,
    StockSerializer,
    StorageLocationSerializer,
    SupplierSerializer,
)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar fornecedores.
    """

    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "company_name", "email", "cnpj"]

    def get_queryset(self):
        return Supplier.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar categorias.
    """

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StorageLocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar locais de armazenamento.
    """

    serializer_class = StorageLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StorageLocation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StockViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar estoques.
    """

    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["product", "local"]

    def get_queryset(self):
        return Stock.objects.filter(product__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar produtos.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_public", "categories"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "stock", "created_at"]

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def movement(self, request, pk=None):
        """
        Registra uma nova movimentação para o produto.
        """
        product = self.get_object()
        serializer = ProductMovementSerializer(data=request.data)

        if serializer.is_valid():
            movement_type = serializer.validated_data["type"]
            quantity = serializer.validated_data["quantity"]

            stock = Stock.objects.filter(product=product).first()
            if not stock:
                default_local = StorageLocation.objects.filter(user=request.user, is_active=True).first()
                if not default_local:
                    return Response(
                        {"error": "Nenhum local de armazenamento disponível."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                stock = Stock.objects.create(product=product, local=default_local)

            if movement_type == "OUT" and stock.quantidade_atual < quantity:
                return Response(
                    {"error": "Estoque insuficiente para esta saída."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save(product=product)

            if movement_type == "IN":
                stock.quantidade_atual += quantity
            else:
                stock.quantidade_atual -= quantity
            stock.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def export(self, request, *args, **kwargs):
        """Exporta produtos do usuário como CSV."""
        products = (
            Product.objects.filter(user=request.user)
            .select_related("supplier")
            .prefetch_related("categories")
        )

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="produtos.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "nome",
            "descricao",
            "preco",
            "preco_custo",
            "estoque",
            "estoque_minimo",
            "categorias",
            "fornecedor",
            "publico",
            "criado_em",
            "atualizado_em",
        ])

        rows = 0
        try:
            products_with_stock = products.annotate(
                _export_stock=Coalesce(
                    Subquery(
                        Stock.objects.filter(product=OuterRef("pk"))
                        .values("product")
                        .annotate(total=Sum("quantidade_atual"))
                        .values("total")[:1]
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
                _export_min_stock=Coalesce(
                    Subquery(
                        Stock.objects.filter(product=OuterRef("pk"))
                        .values("product")
                        .annotate(total=Sum("estoque_minimo"))
                        .values("total")[:1]
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
            for product in products_with_stock:
                categories_str = "|".join(product.categories.values_list("name", flat=True))
                writer.writerow([
                    product.name,
                    product.description,
                    str(product.price),
                    str(product.cost_price),
                    product._export_stock,
                    product._export_min_stock,
                    categories_str,
                    product.supplier.name if product.supplier else "",
                    "sim" if product.is_public else "nao",
                    product.created_at.strftime("%d/%m/%Y %H:%M"),
                    product.updated_at.strftime("%d/%m/%Y %H:%M"),
                ])
                rows += 1

            ExportLog.objects.create(
                user=request.user,
                filename="produtos.csv",
                rows_exported=rows,
                status="SUCCESS",
            )
        except Exception as exc:
            ExportLog.objects.create(
                user=request.user,
                filename="produtos.csv",
                rows_exported=rows,
                status="FAILED",
                error_details=str(exc),
            )
            raise

        return response

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def import_csv(self, request, *args, **kwargs):
        """Importa produtos a partir de um arquivo CSV."""
        serializer = ProductImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        csv_file = serializer.validated_data["file"]

        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "Formato inválido. Envie um arquivo CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            decoded_file = csv_file.read().decode("utf-8-sig")
        except (UnicodeDecodeError, UnicodeError):
            try:
                csv_file.seek(0)
                decoded_file = csv_file.read().decode("latin-1")
            except (UnicodeDecodeError, UnicodeError) as exc:
                ImportLog.objects.create(
                    user=request.user,
                    filename=csv_file.name,
                    rows_processed=0,
                    rows_failed=0,
                    status="FAILED",
                    error_details=f"Erro de codificação: {exc}",
                )
                return Response(
                    {"error": "Erro de codificação do arquivo. Use UTF-8 ou Latin-1."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        reader = csv.DictReader(io.StringIO(decoded_file))

        if not reader.fieldnames:
            ImportLog.objects.create(
                user=request.user,
                filename=csv_file.name,
                rows_processed=0,
                rows_failed=0,
                status="FAILED",
                error_details="Arquivo CSV vazio ou sem cabeçalho.",
            )
            return Response(
                {"error": "Arquivo CSV vazio ou sem cabeçalho."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected_headers = {
            "nome", "descricao", "preco", "preco_custo",
            "estoque", "estoque_minimo", "categorias", "fornecedor", "publico",
        }
        sent_headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing = expected_headers - sent_headers
        if missing:
            ImportLog.objects.create(
                user=request.user,
                filename=csv_file.name,
                rows_processed=0,
                rows_failed=0,
                status="FAILED",
                error_details=f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}",
            )
            return Response(
                {"error": f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows_processed = 0
        rows_failed = 0
        errors = []

        for line_num, row in enumerate(reader, start=2):
            row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
            row_errors = []

            name = row.get("nome", "")
            if not name:
                row_errors.append("nome é obrigatório")

            price_raw = row.get("preco", "0").replace(",", ".")
            cost_raw = row.get("preco_custo", "0").replace(",", ".")

            try:
                price = round(float(price_raw), 2)
            except (ValueError, TypeError):
                row_errors.append(f"preço inválido: '{row.get('preco', '')}'")
                price = 0

            try:
                cost_price = round(float(cost_raw), 2)
            except (ValueError, TypeError):
                row_errors.append(f"preço de custo inválido: '{row.get('preco_custo', '')}'")
                cost_price = 0

            try:
                stock = int(row.get("estoque", 0))
            except (ValueError, TypeError):
                row_errors.append(f"estoque inválido: '{row.get('estoque', '')}'")
                stock = 0

            try:
                min_stock = int(row.get("estoque_minimo", 0))
            except (ValueError, TypeError):
                row_errors.append(f"estoque mínimo inválido: '{row.get('estoque_minimo', '')}'")
                min_stock = 0

            if row_errors:
                errors.append(f"Linha {line_num}: {'; '.join(row_errors)}")
                rows_failed += 1
                continue

            with transaction.atomic():
                supplier_name = row.get("fornecedor", "")
                supplier = None
                if supplier_name:
                    supplier, _ = Supplier.objects.get_or_create(
                        user=request.user,
                        name__iexact=supplier_name,
                        defaults={"user": request.user, "name": supplier_name},
                    )

                product = Product.objects.create(
                    user=request.user,
                    supplier=supplier,
                    name=name,
                    description=row.get("descricao", ""),
                    price=price,
                    cost_price=cost_price,
                    is_public=row.get("publico", "").strip().lower() in ("sim", "true", "1", "s"),
                )

                if stock > 0:
                    default_local = StorageLocation.objects.filter(user=request.user, is_active=True).first()
                    if default_local:
                        Stock.objects.create(product=product, local=default_local, quantidade_atual=stock, estoque_minimo=min_stock)

                categories_raw = row.get("categorias", "")
                if categories_raw:
                    cat_names = [c.strip() for c in categories_raw.split("|") if c.strip()]
                    for cat_name in cat_names:
                        category, _ = Category.objects.get_or_create(
                            user=request.user,
                            name__iexact=cat_name,
                            defaults={
                                "user": request.user,
                                "name": cat_name,
                                "slug": slugify(cat_name),
                            },
                        )
                        product.categories.add(category)

            rows_processed += 1

        status_result = "SUCCESS" if rows_failed == 0 else ("PARTIAL" if rows_processed > 0 else "FAILED")

        ImportLog.objects.create(
            user=request.user,
            filename=csv_file.name,
            rows_processed=rows_processed,
            rows_failed=rows_failed,
            status=status_result,
            error_details="\n".join(errors) if errors else "",
        )

        return Response({
            "rows_processed": rows_processed,
            "rows_failed": rows_failed,
            "status": status_result,
            "errors": errors,
        })


class ProductMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para visualizar o histórico de movimentações.
    """

    serializer_class = ProductMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "type"]
    ordering_fields = ["moved_at"]



    def get_queryset(self):
        return ProductMovement.objects.filter(product__user=self.request.user)
