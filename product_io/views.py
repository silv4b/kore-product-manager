import csv
import io

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from django.views import View

from partners.models import Supplier
from products.models import Category, Product

from .models import ExportLog, ImportLog


class ProductExportView(LoginRequiredMixin, View):
    """Exporta produtos do usuário como CSV."""

    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(user=request.user).select_related("supplier").prefetch_related("categories")

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
            for product in products:
                categories_str = "|".join(product.categories.values_list("name", flat=True))
                writer.writerow([
                    product.name,
                    product.description,
                    str(product.price),
                    str(product.cost_price),
                    product.stock,
                    product.min_stock_level,
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


class ProductImportView(LoginRequiredMixin, View):
    """Importa produtos a partir de um arquivo CSV."""

    template_name = "product_io/product_import.html"

    EXPECTED_HEADERS = {
        "nome",
        "descricao",
        "preco",
        "preco_custo",
        "estoque",
        "estoque_minimo",
        "categorias",
        "fornecedor",
        "publico",
    }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Nenhum arquivo enviado.")
            return render(request, self.template_name)

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Formato inválido. Envie um arquivo CSV.")
            return render(request, self.template_name)

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
                messages.error(request, "Erro de codificação do arquivo. Use UTF-8 ou Latin-1.")
                return render(request, self.template_name)

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
            messages.error(request, "Arquivo CSV vazio ou sem cabeçalho.")
            return render(request, self.template_name)

        sent_headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing = self.EXPECTED_HEADERS - sent_headers
        if missing:
            ImportLog.objects.create(
                user=request.user,
                filename=csv_file.name,
                rows_processed=0,
                rows_failed=0,
                status="FAILED",
                error_details=f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}",
            )
            messages.error(
                request,
                f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}.",
            )
            return render(request, self.template_name)

        rows_processed = 0
        rows_failed = 0
        errors: list[str] = []

        for line_num, row in enumerate(reader, start=2):
            row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
            row_errors: list[str] = []

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
                    stock=stock,
                    min_stock_level=min_stock,
                    is_public=row.get("publico", "").strip().lower() in ("sim", "true", "1", "s"),
                )

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

        status = "SUCCESS" if rows_failed == 0 else ("PARTIAL" if rows_processed > 0 else "FAILED")

        ImportLog.objects.create(
            user=request.user,
            filename=csv_file.name,
            rows_processed=rows_processed,
            rows_failed=rows_failed,
            status=status,
            error_details="\n".join(errors) if errors else "",
        )

        context = {
            "rows_processed": rows_processed,
            "rows_failed": rows_failed,
            "errors": errors,
            "status": status,
        }

        if status == "SUCCESS":
            messages.success(request, f"Importação concluída! {rows_processed} produto(s) importado(s).")
        elif status == "PARTIAL":
            messages.warning(
                request,
                f"Importação parcial: {rows_processed} sucesso, {rows_failed} falha(s).",
            )
        else:
            messages.error(
                request,
                f"Importação falhou: {rows_failed} erro(s). Nenhum produto importado.",
            )

        return render(request, self.template_name, context)
