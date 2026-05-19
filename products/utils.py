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
