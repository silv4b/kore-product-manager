from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Min, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CategoryForm, MovementForm, ProductForm
from .models import Category, PriceHistory, Product, ProductMovement


# --- Product Views ---
@login_required
def product_list(request):
    # Lógica para limpar filtros
    if "clear" in request.GET:
        if "filters_dashboard" in request.session:
            del request.session["filters_dashboard"]
        return redirect("product_list")

    # Recuperação de filtros da sessão
    session_filters = request.session.get("filters_dashboard", {})

    q = request.GET.get("q") if "q" in request.GET else session_filters.get("q", "")
    status = request.GET.get("status") if "status" in request.GET else session_filters.get("status", "")
    min_price = request.GET.get("min_price") if "min_price" in request.GET else session_filters.get("min_price", "")
    max_price = request.GET.get("max_price") if "max_price" in request.GET else session_filters.get("max_price", "")
    min_stock = request.GET.get("min_stock") if "min_stock" in request.GET else session_filters.get("min_stock", "")
    max_stock = request.GET.get("max_stock") if "max_stock" in request.GET else session_filters.get("max_stock", "")
    category_id = request.GET.get("category") if "category" in request.GET else session_filters.get("category", "")

    # Parâmetros de Ordenação
    sort_field = request.GET.get("sort", "name")
    sort_direction = request.GET.get("dir", "asc")
    prefix = "" if sort_direction == "asc" else "-"

    # Salva filtros na sessão
    request.session["filters_dashboard"] = {
        "q": q,
        "status": status,
        "category": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "min_stock": min_stock,
        "max_stock": max_stock,
    }

    # QuerySet Base
    products = Product.objects.filter(user=request.user)

    # Filtros
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id:
        products = products.filter(categories__id=category_id)
    if status == "public":
        products = products.filter(is_public=True)
    elif status == "private":
        products = products.filter(is_public=False)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    # Ordenação com Annotate para evitar duplicados
    if sort_field == "category":
        products = products.annotate(sort_key=Min("categories__name")).order_by(f"{prefix}sort_key")
    else:
        valid_fields = {
            "name": "name",
            "price": "price",
            "stock": "stock",
            "status": "is_public",
        }
        target = valid_fields.get(sort_field, "name")
        products = products.order_by(f"{prefix}{target}")

    # Remove duplicatas residuais de filtros M2M
    products = products.distinct()

    # Cálculo de Estatísticas usando agregação do Banco de Dados
    stats = {
        "total_count": products.count(),
        "total_stock": products.aggregate(Sum("stock"))["stock__sum"] or 0,
        "total_value": products.annotate(
            val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())
        ).aggregate(total=Sum("val"))["total"]
        or 0,
    }

    # Determine view mode
    view_mode = "grid"
    if request.user.is_authenticated:
        view_mode = request.user.profile.view_preferences.get("product_list", "grid")
    else:
        view_mode = request.session.get("view_mode_product_list", "grid")

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": Category.objects.filter(user=request.user),
            "stats": stats,
            "title": "Meus Produtos",
            "is_public_view": False,
            "q": q,
            "status": status,
            "category_id": category_id,
            "min_price": min_price,
            "max_price": max_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "view_mode": view_mode,
            "view_context": "product_list",
        },
    )


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, user=request.user)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            form.save_m2m()  # Important for ManyToMany fields
            messages.success(request, f'Produto "{product.name}" criado com sucesso!')
            return redirect("product_list")
    else:
        form = ProductForm(user=request.user)
    return render(request, "products/product_form.html", {"form": form, "title": "Add Product"})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produto "{product.name}" atualizado com sucesso!')
            return redirect("product_list")
    else:
        form = ProductForm(instance=product, user=request.user)
    return render(
        request,
        "products/product_form.html",
        {"form": form, "title": "Edit Product", "product": product},
    )


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == "POST":
        product_name = product.name
        product.delete()
        messages.success(request, f'Produto "{product_name}" removido permanentemente.')
        return redirect("product_list")

    # Se for uma requisição HTMX, renderiza o modal
    if request.headers.get("HX-Request"):
        return render(request, "products/product_delete_modal.html", {"product": product})

    return render(request, "products/product_confirm_delete.html", {"product": product})


@login_required
def product_bulk_action(request):
    """
    Realiza ações em massa (excluir, público, privado) em múltiplos produtos.
    """
    if request.method == "POST":
        product_ids = request.POST.getlist("product_ids")
        action = request.POST.get("action")

        if not product_ids:
            messages.warning(request, "Nenhum produto selecionado.")
            return redirect("product_list")

        # Filtra apenas produtos que pertencem ao usuário logado
        products = Product.objects.filter(id__in=product_ids, user=request.user)
        count = products.count()

        if action == "delete":
            products.delete()
            messages.success(request, f"{count} produtos excluídos com sucesso.")
        elif action == "make_public":
            products.update(is_public=True)
            messages.success(request, f"{count} produtos marcados como Públicos.")
        elif action == "make_private":
            products.update(is_public=False)
            messages.success(request, f"{count} produtos marcados como Privados.")
        elif action == "add_category":
            category_id = request.POST.get("bulk_category_id")
            if category_id:
                category = get_object_or_404(Category, id=category_id, user=request.user)
                for product in products:
                    product.categories.add(category)
                messages.success(
                    request,
                    f"Categoria '{category.name}' adicionada a {count} produtos.",
                )
            else:
                messages.error(request, "Nenhuma categoria selecionada.")
        else:
            messages.error(request, "Ação inválida.")

    return redirect("product_list")


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Se o produto for privado, apenas o dono pode ver (exige estar logado e ser o dono)
    if not product.is_public:
        if not request.user.is_authenticated or product.user != request.user:
            messages.error(request, "Você não tem permissão para ver este produto.")
            return redirect("account_login")

    return render(request, "products/product_detail_modal.html", {"product": product})


def price_history_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Verificação de permissão
    if not product.is_public:
        if not request.user.is_authenticated or product.user != request.user:
            messages.error(request, "Você não tem permissão para ver este produto.")
            return redirect("account_login")

    # Filtros de data
    price_history = product.price_history.all()

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if data_inicio:
        try:
            # Converte string para datetime ingênuo
            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            # Torna o datetime ciente (aware) do fuso horário do projeto
            data_inicio_obj = timezone.make_aware(data_inicio_obj)
            price_history = price_history.filter(changed_at__gte=data_inicio_obj)
        except ValueError:
            pass

    if data_fim:
        try:
            # Converte string para datetime ingênuo
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            # Adiciona 1 dia para incluir todo o dia final (até 23:59:59)
            data_fim_obj = data_fim_obj + timedelta(days=1)
            # Torna o datetime ciente (aware)
            data_fim_obj = timezone.make_aware(data_fim_obj)
            price_history = price_history.filter(changed_at__lt=data_fim_obj)
        except ValueError:
            pass

    return render(
        request,
        "products/price_history.html",
        {
            "product": product,
            "price_history": price_history,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        },
    )


def price_history_overview(request):
    """Dashboard consolidado de histórico de preços de todos os produtos"""
    # Apenas produtos do usuário logado
    if not request.user.is_authenticated:
        messages.error(request, "Você precisa estar logado para acessar esta página.")
        return redirect("account_login")

    # Base Queryset com otimização de prefetch
    user_products = Product.objects.filter(user=request.user).prefetch_related("price_history")

    # Filtro por Termo de Busca (q)
    q = request.GET.get("q", "")
    if q:
        user_products = user_products.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))

    # Filtro por Categoria
    category_id = request.GET.get("category")
    if category_id:
        user_products = user_products.filter(categories__id=category_id)

    # Estatísticas gerais
    total_alteracoes = PriceHistory.objects.filter(product__in=user_products).count()

    # Produto com mais alterações
    produto_mais_alteracoes_obj = (
        user_products.annotate(num_alteracoes=Count("price_history")).order_by("-num_alteracoes").first()
    )
    produto_mais_alteracoes = {
        "produto": produto_mais_alteracoes_obj,
        "count": (
            produto_mais_alteracoes_obj.num_alteracoes  # type: ignore
            if produto_mais_alteracoes_obj
            else 0
        ),
    }

    # Calcular maior aumento e redução percentual
    maior_aumento = {"produto": None, "percentual": 0}
    maior_reducao = {"produto": None, "percentual": 0}

    # Query otimizada para buscar os dois últimos preços de todos os produtos
    from django.db.models import OuterRef, Subquery

    latest_prices = PriceHistory.objects.filter(product=OuterRef("pk")).order_by("-changed_at")
    products_with_prices = user_products.annotate(
        current_price=Subquery(latest_prices.values("price")[:1]),
        previous_price=Subquery(latest_prices.values("price")[1:2]),
    ).filter(previous_price__isnull=False)

    for p in products_with_prices:
        if p.current_price > p.previous_price:  # type: ignore
            percentual = ((p.current_price - p.previous_price) / p.previous_price) * 100  # type: ignore
            if percentual > maior_aumento["percentual"]:
                maior_aumento["percentual"] = percentual
                maior_aumento["produto"] = p
        elif p.current_price < p.previous_price:  # type: ignore
            percentual = ((p.previous_price - p.current_price) / p.previous_price) * 100  # type: ignore
            if percentual > maior_reducao["percentual"]:
                maior_reducao["percentual"] = percentual
                maior_reducao["produto"] = p

    # Média de alterações por produto
    total_produtos = user_products.count()
    media_alteracoes = total_alteracoes / total_produtos if total_produtos > 0 else 0

    # Produtos com seus históricos (para lista principal)
    produtos_com_historico = []
    for product in user_products:
        # Ordenação em Python para aproveitar o prefetch_related e evitar N+1 queries
        history = sorted(product.price_history.all(), key=lambda x: x.changed_at, reverse=True)

        if not history:
            continue

        # Dados para o Sparkline (últimos 10 preços, ordem cronológica)
        history_prices = [float(h.price) for h in history[:10]]
        history_prices.reverse()  # Reverte para o gráfico (do mais antigo para o mais novo)

        # Determinar tendência
        latest = history[0]
        previous = history[1] if len(history) > 1 else None
        trend = "stable"

        if previous:
            if latest.price > previous.price:
                trend = "up"
            elif latest.price < previous.price:
                trend = "down"

        produtos_com_historico.append(
            {
                "produto": product,
                "historico_precos": history_prices,
                "total_alteracoes": len(history),
                "ultima_alteracao": latest,
                "trend": trend,
            }
        )

    # Ordenar por data da última alteração
    produtos_com_historico.sort(
        key=lambda x: x["ultima_alteracao"].changed_at if x["ultima_alteracao"] else datetime.min,
        reverse=True,
    )

    context = {
        "total_alteracoes": total_alteracoes,
        "produto_mais_alteracoes": produto_mais_alteracoes,
        "maior_aumento": maior_aumento,
        "maior_reducao": maior_reducao,
        "media_alteracoes": media_alteracoes,
        "produtos_com_historico": produtos_com_historico,
        "categorias": Category.objects.filter(user=request.user).distinct(),
        "selected_category": int(category_id) if category_id else "",
        "q": q,
    }

    return render(request, "products/price_history_overview.html", context)


def product_movement_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Verificação de permissão
    if not product.is_public:
        if not request.user.is_authenticated or product.user != request.user:
            messages.error(request, "Você não tem permissão para ver este produto.")
            return redirect("account_login")

    movements = product.movements.all()

    # Filtros de data
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo")

    if data_inicio:
        try:
            from datetime import datetime

            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            movements = movements.filter(moved_at__gte=data_inicio_obj)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            data_fim_obj = data_fim_obj + timedelta(days=1)
            movements = movements.filter(moved_at__lt=data_fim_obj)
        except ValueError:
            pass

    if tipo in ["IN", "OUT"]:
        movements = movements.filter(type=tipo)

    view_mode = "table"
    if request.user.is_authenticated:
        view_mode = request.user.profile.view_preferences.get("product_movement", "table")
    else:
        view_mode = request.session.get("view_mode_product_movement", "table")

    return render(
        request,
        "products/product_movement.html",
        {
            "product": product,
            "movements": movements,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "tipo": tipo,
            "view_mode": view_mode,
            "view_context": "product_movement",
        },
    )


def product_movement_overview(request):
    """Dashboard consolidado de movimentações de todos os produtos"""
    if not request.user.is_authenticated:
        messages.error(request, "Você precisa estar logado para acessar esta página.")
        return redirect("account_login")

    # Base Queryset
    user_products = Product.objects.filter(user=request.user)

    # Filtro por Termo de Busca (q)
    q = request.GET.get("q", "")
    if q:
        user_products = user_products.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))

    # Filtro por Categoria
    category_id = request.GET.get("category")
    if category_id:
        user_products = user_products.filter(categories__id=category_id)

    movements = ProductMovement.objects.filter(product__in=user_products).select_related("product")

    # Filtros de data e tipo
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo")

    if data_inicio:
        try:
            from datetime import datetime

            data_inicio_obj = datetime.strptime(data_inicio, "%Y-%m-%d")
            movements = movements.filter(moved_at__gte=data_inicio_obj)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            data_fim_obj = data_fim_obj + timedelta(days=1)
            movements = movements.filter(moved_at__lt=data_fim_obj)
        except ValueError:
            pass

    if tipo in ["IN", "OUT"]:
        movements = movements.filter(type=tipo)

    # Estatísticas
    from django.db.models import Sum

    total_in = movements.filter(type="IN").aggregate(total=Sum("quantity"))["total"] or 0
    total_out = movements.filter(type="OUT").aggregate(total=Sum("quantity"))["total"] or 0

    context = {
        "movements": movements,
        "total_in": total_in,
        "total_out": total_out,
        "q": q,
        "selected_category": int(category_id) if category_id else "",
        "categorias": Category.objects.filter(user=request.user).distinct(),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "tipo": tipo,
        "view_mode": request.user.profile.view_preferences.get("movement_overview", "table"),
        "view_context": "movement_overview",
    }

    return render(request, "products/product_movement_overview.html", context)


@login_required
def movement_select_product(request, type):
    """Tela para buscar e selecionar um produto para realizar entrada ou saída"""
    if type not in ["IN", "OUT"]:
        return redirect("product_movement_overview")

    # Base Queryset
    products = Product.objects.filter(user=request.user)

    # Filtros
    q = request.GET.get("q", "")
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id:
        products = products.filter(categories__id=category_id)
    if status == "public":
        products = products.filter(is_public=True)
    elif status == "private":
        products = products.filter(is_public=False)

    products = products.distinct().order_by("name")

    context = {
        "products": products,
        "type": type,
        "type_display": "Entrada" if type == "IN" else "Saída",
        "categories": Category.objects.filter(user=request.user),
        "q": q,
        "category_id": category_id,
        "status": status,
        "title": f"Selecionar Produto para {('Entrada' if type == 'IN' else 'Saída')}",
        "view_mode": request.user.profile.view_preferences.get("movement_select", "grid"),
        "view_context": "movement_select",
    }
    return render(request, "products/movement_select_product.html", context)


@login_required
def perform_movement(request, pk, type):
    """Tela para registrar a quantidade e motivo da movimentação"""
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if type not in ["IN", "OUT"]:
        return redirect("product_movement_overview")

    if request.method == "POST":
        form = MovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.product = product
            movement.type = type

            # Atualiza o estoque do produto
            if type == "IN":
                product.stock += movement.quantity
            else:
                if product.stock < movement.quantity:
                    messages.error(
                        request,
                        f"Estoque insuficiente para realizar esta saída. Estoque atual: {product.stock}",
                    )
                    return render(
                        request,
                        "products/movement_form.html",
                        {
                            "form": form,
                            "product": product,
                            "type": type,
                            "type_display": "Entrada" if type == "IN" else "Saída",
                        },
                    )
                product.stock -= movement.quantity

            movement.save()
            product.save()

            messages.success(
                request,
                f"{('Entrada' if type == 'IN' else 'Saída')} realizada com sucesso para {product.name}!",
            )
            return redirect("product_movement_overview")
    else:
        form = MovementForm()

    return render(
        request,
        "products/movement_form.html",
        {
            "form": form,
            "product": product,
            "type": type,
            "type_display": "Entrada" if type == "IN" else "Saída",
        },
    )


# --- Category Views ---
@login_required
def category_list(request):
    # 1. Captura os parâmetros da URL (com valores padrão)
    sort_field = request.GET.get("sort", "name")
    sort_direction = request.GET.get("dir", "asc")

    # 2. Mapeia os nomes das colunas do HTML para os campos do Model
    # Isso evita erros se alguém tentar injetar um campo que não existe
    valid_sort_fields = {
        "name": "name",
        "slug": "slug",
        "color": "color",
    }

    # Valida o campo, se não for válido, usa 'name'
    target_field = valid_sort_fields.get(sort_field, "name")

    # 3. Define o prefixo de direção (Django usa '-' para descendente)
    prefix = "" if sort_direction == "asc" else "-"

    # 4. Aplica a ordenação no QuerySet
    categories = Category.objects.filter(user=request.user).order_by(f"{prefix}{target_field}")

    # Determine view mode
    view_mode = "grid"
    if request.user.is_authenticated:
        view_mode = request.user.profile.view_preferences.get("category_list", "grid")
    else:
        view_mode = request.session.get("view_mode_category_list", "grid")

    return render(
        request,
        "products/category_list.html",
        {
            "categories": categories,
            "title": "Categorias",
            "view_mode": view_mode,
            "view_context": "category_list",
        },
    )


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Categoria criada com sucesso!")
            return redirect("category_list")
    else:
        form = CategoryForm(user=request.user)
    return render(
        request,
        "products/category_form.html",
        {"form": form, "title": "Nova Categoria"},
    )


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada com sucesso!")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category, user=request.user)
    return render(
        request,
        "products/category_form.html",
        {"form": form, "title": "Editar Categoria", "category": category},
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Categoria removida com sucesso.")
        return redirect("category_list")
    return render(request, "products/category_confirm_delete.html", {"category": category})


@login_required
def category_duplicate(request, pk):
    original_category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Categoria duplicada com sucesso!")
            return redirect("category_list")
    else:
        # Preenche os dados iniciais, mas limpa o slug para forçar um novo ou alteração
        initial_data = {
            "name": f"{original_category.name} (Copy)",
            "description": original_category.description,
            "color": original_category.color,
            "slug": f"{original_category.slug}-copy",
        }
        form = CategoryForm(initial=initial_data, user=request.user)

    return render(
        request,
        "products/category_form.html",
        {"form": form, "title": "Duplicar Categoria", "is_duplicate": True},
    )


# --- Account & System Views ---
@login_required
def profile_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        user = request.user
        user.username = username
        user.email = email
        user.save()
        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect("profile")
    return render(request, "account/profile.html")


@login_required
def delete_account_view(request):
    if request.method == "POST":
        password = request.POST.get("password")
        user = request.user

        # Verify password
        from django.contrib.auth import authenticate

        authenticated_user = authenticate(username=user.username, password=password)

        if authenticated_user is not None:
            user.delete()
            messages.success(request, "Sua conta foi excluída permanentemente.")
            return redirect("account_login")
        else:
            messages.error(request, "Falha na exclusão: A senha informada está incorreta.")
            return redirect("profile")

    return redirect("profile")


def user_public_catalog(request, username):
    catalog_user = get_object_or_404(User, username=username)
    products = Product.objects.filter(user=catalog_user, is_public=True)

    q = request.GET.get("q")
    if q:
        products = products.filter(name__icontains=q) | products.filter(description__icontains=q)

    category_id = request.GET.get("category")
    if category_id:
        products = products.filter(categories=category_id)

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    min_stock = request.GET.get("min_stock")
    max_stock = request.GET.get("max_stock")
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    products = products.distinct().order_by("-created_at")

    stats = {
        "total_count": products.count(),
        "total_stock": sum(p.stock for p in products),
        "total_value": sum(p.price * p.stock for p in products),
    }

    # Determine view mode
    view_mode = "grid"
    if request.user.is_authenticated:
        view_mode = request.user.profile.view_preferences.get("user_public_catalog", "grid")
    else:
        view_mode = request.session.get("view_mode_user_public_catalog", "grid")

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": Category.objects.filter(user=catalog_user),
            "stats": stats,
            "title": f"Catálogo de {catalog_user.username}",
            "is_public_view": True,
            "q": q,
            "category_id": request.GET.get("category", ""),
            "min_price": min_price,
            "max_price": max_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "view_mode": view_mode,
            "view_context": "user_public_catalog",
        },
    )


def public_product_list(request):
    # Captura de filtros
    q = request.GET.get("q", "")
    category_id = request.GET.get("category", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    min_stock = request.GET.get("min_stock", "")
    max_stock = request.GET.get("max_stock", "")

    # Parâmetros de Ordenação
    sort_field = request.GET.get("sort", "name")
    sort_direction = request.GET.get("dir", "asc")
    prefix = "" if sort_direction == "asc" else "-"

    # QuerySet Inicial
    products = Product.objects.filter(is_public=True)

    # Filtros
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id:
        products = products.filter(categories__id=category_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    # Ordenação com Annotate
    if sort_field == "category":
        products = products.annotate(sort_key=Min("categories__name")).order_by(f"{prefix}sort_key")
    elif sort_field == "user":
        products = products.order_by(f"{prefix}user__username")
    else:
        valid_fields = {"name": "name", "price": "price", "stock": "stock"}
        target = valid_fields.get(sort_field, "name")
        products = products.order_by(f"{prefix}{target}")

    # Distinct final
    products = products.distinct()

    # Estatísticas
    stats = {
        "total_count": products.count(),
        "total_stock": products.aggregate(Sum("stock"))["stock__sum"] or 0,
        "total_value": products.annotate(
            val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())
        ).aggregate(total=Sum("val"))["total"]
        or 0,
    }

    # Determine view mode
    view_mode = "grid"
    if request.user.is_authenticated:
        view_mode = request.user.profile.view_preferences.get("public_product_list", "grid")
    else:
        view_mode = request.session.get("view_mode_public_product_list", "grid")

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": Category.objects.filter(products__is_public=True).distinct(),
            "stats": stats,
            "title": "Catálogo Público",
            "is_public_view": True,
            "q": q,
            "category_id": category_id,
            "min_price": min_price,
            "max_price": max_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "view_mode": view_mode,
            "view_context": "public_product_list",
        },
    )


def toggle_theme(request):
    current_theme = request.session.get("theme", "light")
    new_theme = "dark" if current_theme == "light" else "light"
    request.session["theme"] = new_theme
    if request.user.is_authenticated:
        profile = request.user.profile
        if profile.theme != new_theme:
            profile.theme = new_theme
            profile.save(update_fields=["theme"])
    if request.headers.get("HX-Request"):
        return HttpResponse(status=204)
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def logout_view(request):
    if request.method == "POST":
        theme = request.session.get("theme", "light")
        auth_logout(request)
        request.session["theme"] = theme
        messages.success(request, "Você saiu do sistema.")
        return redirect("account_login")
    return redirect("product_list")


def set_view_mode(request, context, mode):
    if mode in ["grid", "table"]:
        if request.user.is_authenticated:
            profile = request.user.profile
            if not isinstance(profile.view_preferences, dict):
                profile.view_preferences = {}
            if profile.view_preferences.get(context) != mode:
                profile.view_preferences[context] = mode
                profile.save(update_fields=["view_preferences"])
        else:
            request.session[f"view_mode_{context}"] = mode
    if request.headers.get("HX-Request"):
        return HttpResponse(status=204)
    return redirect(request.META.get("HTTP_REFERER", "/"))
