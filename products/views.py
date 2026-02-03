from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Product, Category
from .forms import ProductForm, CategoryForm
from django.contrib import messages


# --- Product Views ---
@login_required
def product_list(request):
    if "clear" in request.GET:
        if "filters_dashboard" in request.session:
            del request.session["filters_dashboard"]
        return redirect("product_list")

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
    category_id = (
        request.GET.get("category")
        if "category" in request.GET
        else session_filters.get("category", "")
    )

    request.session["filters_dashboard"] = {
        "q": q,
        "status": status,
        "category": category_id,
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
    if category_id:
        products = products.filter(categories=category_id)

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

    products = products.distinct().order_by("-created_at")

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
            "categories": Category.objects.all(),
            "stats": stats,
            "q": q,
            "status": status,
            "category_id": category_id,
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
            form.save_m2m()  # Important for ManyToMany fields
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
    if not product.is_public and product.user != request.user:
        messages.error(request, "Você não tem permissão para ver este produto.")
        return redirect("product_list")

    return render(request, "products/product_detail_modal.html", {"product": product})


# --- Category Views ---
@login_required
def category_list(request):
    if "clear" in request.GET:
        if "filters_categories" in request.session:
            del request.session["filters_categories"]
        return redirect("category_list")

    session_filters = request.session.get("filters_categories", {})
    q = request.GET.get("q") if "q" in request.GET else session_filters.get("q", "")

    request.session["filters_categories"] = {"q": q}

    categories = Category.objects.all()
    if q:
        categories = categories.filter(
            models.Q(name__icontains=q)
            | models.Q(description__icontains=q)
            | models.Q(slug__icontains=q)
        )

    categories = categories.order_by("name")
    return render(
        request, "products/category_list.html", {"categories": categories, "q": q}
    )


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria criada com sucesso!")
            return redirect("category_list")
    else:
        form = CategoryForm()
    return render(
        request,
        "products/category_form.html",
        {"form": form, "title": "Nova Categoria"},
    )


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada com sucesso!")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        "products/category_form.html",
        {"form": form, "title": "Editar Categoria", "category": category},
    )


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Categoria removida com sucesso.")
        return redirect("category_list")
    return render(
        request, "products/category_confirm_delete.html", {"category": category}
    )


@login_required
def category_duplicate(request, pk):
    original_category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria duplicada com sucesso!")
            return redirect("category_list")
    else:
        # Preenche os dados iniciais, mas limpa o slug para forçar um novo ou alteração
        initial_data = {
            "name": f"{original_category.name} (Cópia)",
            "description": original_category.description,
            "color": original_category.color,
            "slug": f"{original_category.slug}-copia",
        }
        form = CategoryForm(initial=initial_data)

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
            messages.error(
                request, "Falha na exclusão: A senha informada está incorreta."
            )
            return redirect("profile")

    return redirect("profile")


def public_product_list(request):
    products = Product.objects.filter(is_public=True)
    q = request.GET.get("q")
    if q:
        products = products.filter(name__icontains=q) | products.filter(
            description__icontains=q
        )

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

    return render(
        request,
        "products/product_list.html",
        {
            "products": products,
            "categories": Category.objects.all(),
            "stats": stats,
            "title": "Catálogo Público",
            "is_public_view": True,
            "q": q,
            "category_id": request.GET.get("category", ""),
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


from django.contrib.auth import logout


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
