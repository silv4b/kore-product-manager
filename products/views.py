from datetime import datetime, timedelta
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import CategoryForm, MovementForm, ProductForm
from .models import Category, PriceHistory, Product, ProductMovement
from .utils import PaginationMixin, apply_product_filters, paginate_queryset, sort_queryset


# --- Product Views ---
class ProductListView(LoginRequiredMixin, PaginationMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if "clear" in request.GET:
            if "filters_dashboard" in request.session:
                del request.session["filters_dashboard"]
            return redirect("product_list")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        session_filters = self.request.session.get("filters_dashboard", {})

        self.q = self.request.GET.get("q", session_filters.get("q", ""))
        self.status = self.request.GET.get("status", session_filters.get("status", ""))
        self.min_price = self.request.GET.get("min_price", session_filters.get("min_price", ""))
        self.max_price = self.request.GET.get("max_price", session_filters.get("max_price", ""))
        self.min_stock = self.request.GET.get("min_stock", session_filters.get("min_stock", ""))
        self.max_stock = self.request.GET.get("max_stock", session_filters.get("max_stock", ""))
        self.category_id = self.request.GET.get("category", session_filters.get("category", ""))

        self.sort_field = self.request.GET.get("sort", "name")
        self.sort_direction = self.request.GET.get("dir", "asc")

        self.request.session["filters_dashboard"] = {
            "q": self.q,
            "status": self.status,
            "category": self.category_id,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
        }

        products = cast("Any", Product.objects).for_user(self.request.user)
        products = apply_product_filters(
            products,
            q=self.q,
            category_id=self.category_id,
            status=self.status,
            min_price=self.min_price,
            max_price=self.max_price,
            min_stock=self.min_stock,
            max_stock=self.max_stock,
        )

        valid_fields = {
            "name": "name",
            "price": "price",
            "stock": "stock",
            "status": "is_public",
        }
        products = sort_queryset(
            products, self.sort_field, self.sort_direction, valid_fields, default_sort="name", category_sort_key="categories__name"
        )

        return products.distinct()

    def get_context_data(self, **kwargs):
        full_qs = self.object_list
        context = super().get_context_data(**kwargs)

        context["stats"] = {
            "total_count": full_qs.count(),
            "total_stock": full_qs.aggregate(Sum("stock"))["stock__sum"] or 0,
            "total_value": full_qs.annotate(val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())).aggregate(total=Sum("val"))[
                "total"
            ]
            or 0,
        }
        context["categories"] = Category.objects.filter(user=self.request.user)
        context["title"] = "Meus Produtos"
        context["is_public_view"] = False
        context.update(
            {
                "q": self.q,
                "status": self.status,
                "category_id": self.category_id,
                "min_price": self.min_price,
                "max_price": self.max_price,
                "min_stock": self.min_stock,
                "max_stock": self.max_stock,
            }
        )

        if self.request.user.is_authenticated:
            context["view_mode"] = cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("product_list", "grid")
        else:
            context["view_mode"] = self.request.session.get("view_mode_product_list", "grid")

        context["view_context"] = "product_list"
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    success_url = reverse_lazy("product_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        product = form.save(commit=False)
        product.user = self.request.user
        product.save()
        form.save_m2m()
        messages.success(self.request, f'Produto "{product.name}" criado com sucesso!')
        return cast("Any", super()).form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    success_url = reverse_lazy("product_list")
    object: Product

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = cast("Any", super()).form_valid(form)
        messages.success(self.request, f'Produto "{self.object.name}" atualizado com sucesso!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Product"
        return context


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy("product_list")
    object: Product

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def form_valid(self, form):
        product_name = getattr(self.object, "name", "Produto")
        response = cast("Any", super()).form_valid(form)
        messages.success(self.request, f'Produto "{product_name}" removido permanentemente.')
        return response

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["products/product_delete_modal.html"]
        return ["products/product_confirm_delete.html"]


class ProductBulkActionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        product_ids = request.POST.getlist("product_ids")
        action = request.POST.get("action")

        if not product_ids:
            messages.warning(request, "Nenhum produto selecionado.")
            return redirect("product_list")

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
                messages.success(request, f"Categoria '{category.name}' adicionada a {count} produtos.")
            else:
                messages.error(request, "Nenhuma categoria selecionada.")
        else:
            messages.error(request, "Ação inválida.")

        return redirect("product_list")


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail_modal.html"
    context_object_name = "product"
    object: Product

    def dispatch(self, request, *args, **kwargs):
        self.object = cast("Product", self.get_object())
        if not getattr(self.object, "is_public", False):
            if not request.user.is_authenticated or getattr(self.object, "user", None) != request.user:
                messages.error(request, "Você não tem permissão para ver este produto.")
                return redirect("account_login")
        return super().dispatch(request, *args, **kwargs)


class PriceHistoryView(DetailView):
    model = Product
    template_name = "products/price_history.html"
    context_object_name = "product"
    object: Product

    def dispatch(self, request, *args, **kwargs):
        self.object = cast("Product", self.get_object())
        if not getattr(self.object, "is_public", False):
            if not request.user.is_authenticated or getattr(self.object, "user", None) != request.user:
                messages.error(request, "Você não tem permissão para ver este produto.")
                return redirect("account_login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        price_history = cast("Any", self.object).price_history.all()

        data_inicio = self.request.GET.get("data_inicio")
        data_fim = self.request.GET.get("data_fim")

        if data_inicio:
            try:
                data_inicio_obj = timezone.make_aware(datetime.strptime(data_inicio, "%Y-%m-%d"))
                price_history = price_history.filter(changed_at__gte=data_inicio_obj)
            except ValueError:
                pass

        if data_fim:
            try:
                data_fim_obj = timezone.make_aware(datetime.strptime(data_fim, "%Y-%m-%d")) + timedelta(days=1)
                price_history = price_history.filter(changed_at__lt=data_fim_obj)
            except ValueError:
                pass

        context["price_history"] = price_history
        context["data_inicio"] = data_inicio
        context["data_fim"] = data_fim
        return context


class PriceHistoryOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "products/price_history_overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_products = Product.objects.filter(user=self.request.user).prefetch_related("price_history")

        q = self.request.GET.get("q", "")
        if q:
            user_products = user_products.filter(models.Q(name__icontains=q) | models.Q(description__icontains=q))

        category_id = self.request.GET.get("category")
        if category_id:
            user_products = user_products.filter(categories__id=category_id)

        total_alteracoes = PriceHistory.objects.filter(product__in=user_products).count()

        produto_mais_alteracoes_obj = user_products.annotate(num_alteracoes=Count("price_history")).order_by("-num_alteracoes").first()
        produto_mais_alteracoes = {
            "produto": produto_mais_alteracoes_obj,
            "count": getattr(produto_mais_alteracoes_obj, "num_alteracoes", 0) if produto_mais_alteracoes_obj else 0,
        }

        maior_aumento = {"produto": None, "percentual": 0}
        maior_reducao = {"produto": None, "percentual": 0}

        latest_prices = PriceHistory.objects.filter(product=OuterRef("pk")).order_by("-changed_at")
        products_with_prices = user_products.annotate(
            current_price=Subquery(latest_prices.values("price")[:1]),
            previous_price=Subquery(latest_prices.values("price")[1:2]),
        ).filter(previous_price__isnull=False)

        for p in products_with_prices:
            current_price = getattr(p, "current_price", 0)
            previous_price = getattr(p, "previous_price", 0)

            if current_price > previous_price:
                percentual = ((current_price - previous_price) / previous_price) * 100
                if percentual > maior_aumento["percentual"]:
                    maior_aumento["percentual"] = percentual
                    maior_aumento["produto"] = p  # type: ignore
            elif current_price < previous_price:
                percentual = ((previous_price - current_price) / previous_price) * 100
                if percentual > maior_reducao["percentual"]:
                    maior_reducao["percentual"] = percentual
                    maior_reducao["produto"] = p  # type: ignore

        total_produtos = user_products.count()
        media_alteracoes = total_alteracoes / total_produtos if total_produtos > 0 else 0

        produtos_com_historico = []
        for product in user_products:
            history = sorted(cast("Any", product).price_history.all(), key=lambda x: x.changed_at, reverse=True)
            if not history:
                continue

            history_prices = [float(h.price) for h in history[:10]]
            history_prices.reverse()

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

        produtos_com_historico.sort(
            key=lambda x: x["ultima_alteracao"].changed_at if x["ultima_alteracao"] else datetime.min,
            reverse=True,
        )

        page_obj, pagination_ctx = paginate_queryset(produtos_com_historico, self.request)

        context.update(
            {
                "total_alteracoes": total_alteracoes,
                "produto_mais_alteracoes": produto_mais_alteracoes,
                "maior_aumento": maior_aumento,
                "maior_reducao": maior_reducao,
                "media_alteracoes": media_alteracoes,
                "produtos_com_historico": page_obj,
                "categorias": Category.objects.filter(user=self.request.user).distinct(),
                "selected_category": int(category_id) if category_id else "",
                "q": q,
            }
        )
        context.update(pagination_ctx)
        return context


class ProductMovementView(DetailView):
    model = Product
    template_name = "products/product_movement.html"
    context_object_name = "product"
    object: Product

    def dispatch(self, request, *args, **kwargs):
        self.object = cast("Product", self.get_object())
        if not getattr(self.object, "is_public", False):
            if not request.user.is_authenticated or getattr(self.object, "user", None) != request.user:
                messages.error(request, "Você não tem permissão para ver este produto.")
                return redirect("account_login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movements = cast("Any", self.object).movements.all()

        data_inicio = self.request.GET.get("data_inicio")
        data_fim = self.request.GET.get("data_fim")
        tipo = self.request.GET.get("tipo")

        if data_inicio:
            try:
                data_inicio_obj = timezone.make_aware(datetime.strptime(data_inicio, "%Y-%m-%d"))
                movements = movements.filter(moved_at__gte=data_inicio_obj)
            except ValueError:
                pass

        if data_fim:
            try:
                data_fim_obj = timezone.make_aware(datetime.strptime(data_fim, "%Y-%m-%d")) + timedelta(days=1)
                movements = movements.filter(moved_at__lt=data_fim_obj)
            except ValueError:
                pass

        if tipo in ["IN", "OUT"]:
            movements = movements.filter(type=tipo)

        if self.request.user.is_authenticated:
            view_mode = cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("product_movement", "table")
        else:
            view_mode = self.request.session.get("view_mode_product_movement", "table")

        context.update(
            {
                "movements": movements,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "tipo": tipo,
                "view_mode": view_mode,
                "view_context": "product_movement",
            }
        )
        return context


class ProductMovementOverviewView(LoginRequiredMixin, PaginationMixin, ListView):
    model = ProductMovement
    template_name = "products/product_movement_overview.html"
    context_object_name = "movements"
    paginate_by = 20

    def get_queryset(self):
        user_products = Product.objects.filter(user=self.request.user)

        self.q = self.request.GET.get("q", "")
        if self.q:
            user_products = user_products.filter(models.Q(name__icontains=self.q) | models.Q(description__icontains=self.q))

        self.category_id = self.request.GET.get("category")
        if self.category_id:
            user_products = user_products.filter(categories__id=self.category_id)

        movements = ProductMovement.objects.filter(product__in=user_products).select_related("product")

        self.data_inicio = self.request.GET.get("data_inicio")
        self.data_fim = self.request.GET.get("data_fim")
        self.tipo = self.request.GET.get("tipo")

        if self.data_inicio:
            try:
                data_inicio_obj = timezone.make_aware(datetime.strptime(self.data_inicio, "%Y-%m-%d"))
                movements = movements.filter(moved_at__gte=data_inicio_obj)
            except ValueError:
                pass

        if self.data_fim:
            try:
                data_fim_obj = timezone.make_aware(datetime.strptime(self.data_fim, "%Y-%m-%d")) + timedelta(days=1)
                movements = movements.filter(moved_at__lt=data_fim_obj)
            except ValueError:
                pass

        if self.tipo in ["IN", "OUT"]:
            movements = movements.filter(type=self.tipo)

        return movements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movements = self.get_queryset()

        total_in = movements.filter(type="IN").aggregate(total=Sum("quantity"))["total"] or 0
        total_out = movements.filter(type="OUT").aggregate(total=Sum("quantity"))["total"] or 0

        context.update(
            {
                "total_in": total_in,
                "total_out": total_out,
                "q": self.q,
                "selected_category": int(self.category_id) if self.category_id else "",
                "categorias": Category.objects.filter(user=self.request.user).distinct(),
                "data_inicio": self.data_inicio,
                "data_fim": self.data_fim,
                "tipo": self.tipo,
                "view_mode": cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("movement_overview", "table"),
                "view_context": "movement_overview",
            }
        )
        return context


class MovementSelectProductView(LoginRequiredMixin, PaginationMixin, ListView):
    model = Product
    template_name = "products/movement_select_product.html"
    context_object_name = "products"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.type = kwargs.get("type")
        if self.type not in ["IN", "OUT"]:
            return redirect("product_movement_overview")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        products = cast("Any", Product.objects).for_user(self.request.user)

        self.q = self.request.GET.get("q", "")
        self.category_id = self.request.GET.get("category", "")
        self.status = self.request.GET.get("status", "")

        products = apply_product_filters(products, q=self.q, category_id=self.category_id, status=self.status)
        return products.distinct().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "type": self.type,
                "type_display": "Entrada" if self.type == "IN" else "Saída",
                "categories": Category.objects.filter(user=self.request.user),
                "q": self.q,
                "category_id": self.category_id,
                "status": self.status,
                "title": f"Selecionar Produto para {('Entrada' if self.type == 'IN' else 'Saída')}",
                "view_mode": cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("movement_select", "grid"),
                "view_context": "movement_select",
            }
        )
        return context


class PerformMovementView(LoginRequiredMixin, CreateView):
    model = ProductMovement
    form_class = MovementForm
    template_name = "products/movement_form.html"
    success_url = reverse_lazy("product_movement_overview")

    def dispatch(self, request, *args, **kwargs):
        self.product_obj = get_object_or_404(Product, pk=kwargs.get("pk"), user=request.user)
        self.type = kwargs.get("type")
        if self.type not in ["IN", "OUT"]:
            return redirect("product_movement_overview")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        movement = form.save(commit=False)
        movement.product = self.product_obj
        movement.type = self.type

        if self.type == "IN":
            self.product_obj.stock += movement.quantity
        else:
            if self.product_obj.stock < movement.quantity:
                messages.error(
                    self.request,
                    f"Estoque insuficiente para realizar esta saída. Estoque atual: {self.product_obj.stock}",
                )
                return self.form_invalid(form)
            self.product_obj.stock -= movement.quantity

        movement.save()
        self.product_obj.save()

        messages.success(
            self.request,
            f"{('Entrada' if self.type == 'IN' else 'Saída')} realizada com sucesso para {self.product_obj.name}!",
        )
        return cast("Any", super()).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "product": self.product_obj,
                "type": self.type,
                "type_display": "Entrada" if self.type == "IN" else "Saída",
            }
        )
        return context


# --- Category Views ---
class CategoryListView(LoginRequiredMixin, PaginationMixin, ListView):
    model = Category
    template_name = "products/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        sort_field = self.request.GET.get("sort", "name")
        sort_direction = self.request.GET.get("dir", "asc")

        valid_sort_fields = {"name": "name", "slug": "slug", "color": "color"}
        target_field = valid_sort_fields.get(sort_field, "name")
        prefix = "" if sort_direction == "asc" else "-"

        return Category.objects.filter(user=self.request.user).order_by(f"{prefix}{target_field}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            view_mode = cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("category_list", "grid")
        else:
            view_mode = self.request.session.get("view_mode_category_list", "grid")

        context.update(
            {
                "title": "Categorias",
                "view_mode": view_mode,
                "view_context": "category_list",
            }
        )
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/category_form.html"
    success_url = reverse_lazy("category_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        category = form.save(commit=False)
        category.user = self.request.user
        category.save()
        messages.success(self.request, "Categoria criada com sucesso!")
        return cast("Any", super()).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Nova Categoria"
        return context


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "products/category_form.html"
    success_url = reverse_lazy("category_list")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = cast("Any", super()).form_valid(form)
        messages.success(self.request, "Categoria atualizada com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Editar Categoria"
        return context


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "products/category_confirm_delete.html"
    success_url = reverse_lazy("category_list")

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = cast("Any", super()).form_valid(form)
        messages.success(self.request, "Categoria removida com sucesso.")
        return response


class CategoryDuplicateView(LoginRequiredMixin, FormView):
    form_class = CategoryForm
    template_name = "products/category_form.html"
    success_url = reverse_lazy("category_list")

    def dispatch(self, request, *args, **kwargs):
        self.original_category = get_object_or_404(Category, pk=kwargs.get("pk"), user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            {
                "name": f"{self.original_category.name} (Copy)",
                "description": self.original_category.description,
                "color": self.original_category.color,
                "slug": f"{self.original_category.slug}-copy",
            }
        )
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        category = form.save(commit=False)
        category.user = self.request.user
        category.save()
        messages.success(self.request, "Categoria duplicada com sucesso!")
        return cast("Any", super()).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Duplicar Categoria"
        context["is_duplicate"] = True
        return context


# --- Account & System Views ---
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        email = request.POST.get("email")
        user = request.user
        user.username = username
        user.email = email
        cast("Any", user).save()
        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect("profile")


class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        password = request.POST.get("password")
        user = request.user

        from django.contrib.auth import authenticate

        authenticated_user = authenticate(username=getattr(user, "username", ""), password=password)

        if authenticated_user is not None:
            cast("Any", user).delete()
            messages.success(request, "Sua conta foi excluída permanentemente.")
            return redirect("account_login")
        else:
            messages.error(request, "Falha na exclusão: A senha informada está incorreta.")
            return redirect("profile")


class UserPublicCatalogView(PaginationMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.catalog_user = get_object_or_404(User, username=kwargs.get("username"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        products = cast("Any", Product.objects).for_user(self.catalog_user).filter(is_public=True)

        self.q = self.request.GET.get("q")
        self.category_id = self.request.GET.get("category")
        self.min_price = self.request.GET.get("min_price")
        self.max_price = self.request.GET.get("max_price")
        self.min_stock = self.request.GET.get("min_stock")
        self.max_stock = self.request.GET.get("max_stock")

        products = apply_product_filters(
            products,
            q=self.q,
            category_id=self.category_id,
            min_price=self.min_price,
            max_price=self.max_price,
            min_stock=self.min_stock,
            max_stock=self.max_stock,
        )

        return products.distinct().order_by("-created_at")

    def get_context_data(self, **kwargs):
        full_qs = self.object_list
        context = super().get_context_data(**kwargs)

        stats = {
            "total_count": full_qs.count(),
            "total_stock": full_qs.aggregate(Sum("stock"))["stock__sum"] or 0,
            "total_value": full_qs.annotate(val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())).aggregate(total=Sum("val"))[
                "total"
            ]
            or 0,
        }

        if self.request.user.is_authenticated:
            view_mode = cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("user_public_catalog", "grid")
        else:
            view_mode = self.request.session.get("view_mode_user_public_catalog", "grid")

        context.update(
            {
                "categories": Category.objects.filter(user=self.catalog_user),
                "stats": stats,
                "title": f"Catálogo de {self.catalog_user.username}",
                "is_public_view": True,
                "q": self.q,
                "category_id": self.category_id,
                "min_price": self.min_price,
                "max_price": self.max_price,
                "min_stock": self.min_stock,
                "max_stock": self.max_stock,
                "view_mode": view_mode,
                "view_context": "user_public_catalog",
            }
        )
        return context


class PublicProductListView(PaginationMixin, ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        self.q = self.request.GET.get("q", "")
        self.category_id = self.request.GET.get("category", "")
        self.min_price = self.request.GET.get("min_price", "")
        self.max_price = self.request.GET.get("max_price", "")
        self.min_stock = self.request.GET.get("min_stock", "")
        self.max_stock = self.request.GET.get("max_stock", "")

        sort_field = self.request.GET.get("sort", "name")
        sort_direction = self.request.GET.get("dir", "asc")

        products = Product.objects.filter(is_public=True)

        products = apply_product_filters(
            products,
            q=self.q,
            category_id=self.category_id,
            min_price=self.min_price,
            max_price=self.max_price,
            min_stock=self.min_stock,
            max_stock=self.max_stock,
        )

        valid_fields = {"name": "name", "price": "price", "stock": "stock", "user": "user__username"}
        products = sort_queryset(products, sort_field, sort_direction, valid_fields, default_sort="name", category_sort_key="categories__name")

        return products.distinct()

    def get_context_data(self, **kwargs):
        full_qs = self.object_list
        context = super().get_context_data(**kwargs)

        stats = {
            "total_count": full_qs.count(),
            "total_stock": full_qs.aggregate(Sum("stock"))["stock__sum"] or 0,
            "total_value": full_qs.annotate(val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())).aggregate(total=Sum("val"))[
                "total"
            ]
            or 0,
        }

        if self.request.user.is_authenticated:
            view_mode = cast("Any", getattr(cast("Any", self.request.user), "profile", None)).view_preferences.get("public_product_list", "grid")
        else:
            view_mode = self.request.session.get("view_mode_public_product_list", "grid")

        context.update(
            {
                "categories": Category.objects.filter(products__is_public=True).distinct(),
                "stats": stats,
                "title": "Catálogo Público",
                "is_public_view": True,
                "q": self.q,
                "category_id": self.category_id,
                "min_price": self.min_price,
                "max_price": self.max_price,
                "min_stock": self.min_stock,
                "max_stock": self.max_stock,
                "view_mode": view_mode,
                "view_context": "public_product_list",
            }
        )
        return context


class ToggleThemeView(View):
    def get(self, request, *args, **kwargs):
        return self._toggle(request)

    def post(self, request, *args, **kwargs):
        return self._toggle(request)

    def _toggle(self, request):
        current_theme = request.session.get("theme", "light")
        new_theme = "dark" if current_theme == "light" else "light"
        request.session["theme"] = new_theme
        if request.user.is_authenticated:
            profile = getattr(cast("Any", request.user), "profile", None)
            if profile and getattr(profile, "theme", None) != new_theme:
                profile.theme = new_theme
                cast("Any", profile).save(update_fields=["theme"])
        if request.headers.get("HX-Request"):
            return HttpResponse(status=204)
        return redirect(request.META.get("HTTP_REFERER", "/"))


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        return self._logout(request)

    def post(self, request, *args, **kwargs):
        return self._logout(request)

    def _logout(self, request):
        theme = request.session.get("theme", "light")
        auth_logout(request)
        request.session["theme"] = theme
        messages.success(request, "Você saiu do sistema.")
        return redirect("account_login")


class SetViewModeView(View):
    def get(self, request, context, mode, *args, **kwargs):
        if mode in ["grid", "table"]:
            if request.user.is_authenticated:
                profile = getattr(cast("Any", request.user), "profile", None)
                if profile:
                    if not isinstance(getattr(profile, "view_preferences", None), dict):
                        profile.view_preferences = {}
                    if cast("Any", profile).view_preferences.get(context) != mode:
                        cast("Any", profile).view_preferences[context] = mode
                        cast("Any", profile).save(update_fields=["view_preferences"])
            else:
                request.session[f"view_mode_{context}"] = mode
        if request.headers.get("HX-Request"):
            return HttpResponse(status=204)
        return redirect(request.META.get("HTTP_REFERER", "/"))


# --- Supplier Redirect ---
def supplier_list_redirect(request):
    return redirect("partner_supplier_list")


# --- Report Views ---
class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "products/report_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_products = Product.objects.filter(user=self.request.user)

        # Valor total do estoque a preço de custo.
        total_cost_value = user_products.annotate(
            val=ExpressionWrapper(F("cost_price") * F("stock"), output_field=DecimalField())
        ).aggregate(total=Sum("val"))["total"] or 0

        # Valor total do estoque a preço de venda.
        total_sales_value = user_products.annotate(
            val=ExpressionWrapper(F("price") * F("stock"), output_field=DecimalField())
        ).aggregate(total=Sum("val"))["total"] or 0

        # Lucro potencial total
        potential_profit = total_sales_value - total_cost_value

        # Produtos Mais Vendidos baseados no histórico de saídas (ProductMovement OUT)
        top_selling_movements = ProductMovement.objects.filter(
            product__user=self.request.user,
            type="OUT"
        ).values("product__name", "product__price", "product__cost_price").annotate(
            total_sold=Sum("quantity"),
            total_revenue=Sum(ExpressionWrapper(F("quantity") * F("product__price"), output_field=DecimalField())),
            total_cost=Sum(ExpressionWrapper(F("quantity") * F("product__cost_price"), output_field=DecimalField()))
        ).annotate(
            total_profit=ExpressionWrapper(F("total_revenue") - F("total_cost"), output_field=DecimalField())
        ).order_by("-total_sold")[:5]

        context.update({
            "title": "Relatório de Giro e Lucratividade",
            "total_cost_value": total_cost_value,
            "total_sales_value": total_sales_value,
            "potential_profit": potential_profit,
            "top_selling_products": top_selling_movements,
        })
        return context
