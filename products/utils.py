from django.core.paginator import Paginator
from django.db.models import Min, Q


def apply_product_filters(
    queryset,
    q=None,
    category_id=None,
    status=None,
    min_price=None,
    max_price=None,
    min_stock=None,
    max_stock=None,
):
    """Aplica os filtros padrão para queries de Produto."""
    if q:
        queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id:
        queryset = queryset.filter(categories__id=category_id)
    if status == "public":
        queryset = queryset.filter(is_public=True)
    elif status == "private":
        queryset = queryset.filter(is_public=False)
    if min_price:
        queryset = queryset.filter(price__gte=min_price)
    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    if min_stock:
        queryset = queryset.filter(stock__gte=min_stock)
    if max_stock:
        queryset = queryset.filter(stock__lte=max_stock)
    return queryset


PAGE_SIZES = [20, 50, 100]


class PaginationMixin:
    paginate_by = 20
    page_sizes = PAGE_SIZES

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get("page_size")
        if page_size and page_size.isdigit():
            size = int(page_size)
            if size in self.page_sizes:
                return size
        return self.paginate_by

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_size = self.get_paginate_by(None)
        context["page_sizes"] = self.page_sizes
        context["page_size"] = page_size
        return context


def paginate_queryset(queryset, request, per_page=20, page_sizes=None):
    """Utility for paginating querysets manually (used in FBVs)."""
    if page_sizes is None:
        page_sizes = PAGE_SIZES
    page_size = request.GET.get("page_size", "")
    if page_size.isdigit():
        size = int(page_size)
        if size not in page_sizes:
            size = per_page
    else:
        size = per_page

    paginator = Paginator(queryset, size)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return page_obj, {
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": paginator.num_pages > 1,
        "page_sizes": page_sizes,
        "page_size": size,
    }


def sort_queryset(queryset, sort_field, sort_direction, valid_fields, default_sort="name", category_sort_key=None):
    """
    Ordena um queryset baseado em parâmetros de requisição.
    :param category_sort_key: Se fornecido e sort_field == 'category', usa Annotate para ordenar.
    """
    prefix = "" if sort_direction == "asc" else "-"

    if sort_field == "category" and category_sort_key:
        # Ex: category_sort_key = "categories__name"
        return queryset.annotate(sort_key=Min(category_sort_key)).order_by(f"{prefix}sort_key")

    target = valid_fields.get(sort_field, default_sort)
    return queryset.order_by(f"{prefix}{target}")
