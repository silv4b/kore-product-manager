from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductForm
from django.contrib import messages


@login_required
def product_list(request):
    # Se o parâmetro 'clear' estiver presente, limpa os filtros da sessão
    if "clear" in request.GET:
        if "filters_dashboard" in request.session:
            del request.session["filters_dashboard"]
        return redirect("product_list")

    # Pega filtros da URL ou da Sessão (Sticky Filters)
    session_filters = request.session.get("filters_dashboard", {})

    q = request.GET.get("q") if "q" in request.GET else session_filters.get("q", "")
    status = (
        request.GET.get("status")
        if "status" in request.GET
        else session_filters.get("status", "")
    )
    min_price = (
        request.GET.get("min_price")
        if "min_price" in request.GET
        else session_filters.get("min_price", "")
    )
    max_price = (
        request.GET.get("max_price")
        if "max_price" in request.GET
        else session_filters.get("max_price", "")
    )
    min_stock = (
        request.GET.get("min_stock")
        if "min_stock" in request.GET
        else session_filters.get("min_stock", "")
    )
    max_stock = (
        request.GET.get("max_stock")
        if "max_stock" in request.GET
        else session_filters.get("max_stock", "")
    )

    # Salva os estados atuais na sessão para a próxima visita
    request.session["filters_dashboard"] = {
        "q": q,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "min_stock": min_stock,
        "max_stock": max_stock,
    }

    products = Product.objects.filter(user=request.user)

    if q:
        products = products.filter(name__icontains=q) | products.filter(
            description__icontains=q
        )
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

    products = products.order_by("-created_at")

    # Estatísticas básicas para o Dashboard
    stats = {
        "total_count": products.count(),
        "total_stock": sum(p.stock for p in products),
        "total_value": sum(p.price * p.stock for p in products),
    }

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "stats": stats,
            "q": q,
            "status": status,
            "min_price": min_price,
            "max_price": max_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
        },
    )


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, f'Produto "{product.name}" criado com sucesso!')
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(
        request, "products/product_form.html", {"form": form, "title": "Add Product"}
    )


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Produto "{product.name}" atualizado com sucesso!'
            )
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
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
    return render(request, "products/product_confirm_delete.html", {"product": product})


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Verifica se o produto é público ou se pertence ao usuário
    if not product.is_public and product.user != request.user:
        messages.error(request, "Você não tem permissão para ver este produto.")
        return redirect("product_list")

    return render(request, "products/product_detail_modal.html", {"product": product})


from django.contrib.auth import logout


@login_required
def profile_view(request):
    if request.method == "POST":
        # Update User Email/Username
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
        user = request.user
        user.delete()
        messages.success(request, "Sua conta foi excluída permanentemente.")
        return redirect("account_login")
    return redirect("profile")


def public_product_list(request):
    products = Product.objects.filter(is_public=True)

    # Search
    q = request.GET.get("q")
    if q:
        products = products.filter(name__icontains=q) | products.filter(
            description__icontains=q
        )

    # Price Filter
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Stock Filter
    min_stock = request.GET.get("min_stock")
    max_stock = request.GET.get("max_stock")
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    products = products.order_by("-created_at")

    # Estatísticas básicas para o Catálogo
    stats = {
        "total_count": products.count(),
        "total_stock": sum(p.stock for p in products),
        "total_value": sum(p.price * p.stock for p in products),
    }

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "stats": stats,
            "title": "Catálogo Público",
            "is_public_view": True,
            "q": q,
            "min_price": min_price,
            "max_price": max_price,
            "min_stock": min_stock,
            "max_stock": max_stock,
        },
    )


def toggle_theme(request):
    current_theme = request.session.get("theme", "light")
    new_theme = "dark" if current_theme == "light" else "light"
    request.session["theme"] = new_theme

    if request.user.is_authenticated:
        profile = request.user.profile
        profile.theme = new_theme
        profile.save()

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def logout_view(request):
    if request.method == "POST":
        theme = request.session.get("theme", "light")
        logout(request)
        request.session["theme"] = theme
        messages.success(request, "Você saiu do sistema.")
        return redirect("account_login")
    return redirect("product_list")


def set_view_mode(request, mode):
    if mode in ["grid", "table"]:
        request.session["view_mode"] = mode
    return redirect(request.META.get("HTTP_REFERER", "/"))
