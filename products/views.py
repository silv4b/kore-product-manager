from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductForm
from django.contrib import messages

@login_required
def product_list(request):
    products = Product.objects.filter(user=request.user)

    # Search
    q = request.GET.get('q')
    if q:
        products = products.filter(name__icontains=q) | products.filter(description__icontains=q)

    # Status Filter
    status = request.GET.get('status')
    if status == 'public':
        products = products.filter(is_public=True)
    elif status == 'private':
        products = products.filter(is_public=False)

    # Price Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Stock Filter
    min_stock = request.GET.get('min_stock')
    max_stock = request.GET.get('max_stock')
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    products = products.order_by('-created_at')

    return render(request, 'products/product_list.html', {
        'products': products,
        'q': q,
        'status': status,
        'min_price': min_price,
        'max_price': max_price,
        'min_stock': min_stock,
        'max_stock': max_stock,
    })

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            messages.success(request, f'Produto "{product.name}" criado com sucesso!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produto "{product.name}" atualizado com sucesso!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Produto "{product_name}" removido permanentemente.')
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})

from django.contrib.auth import logout

@login_required
def profile_view(request):
    if request.method == 'POST':
        # Update User Email/Username
        username = request.POST.get('username')
        email = request.POST.get('email')

        user = request.user
        user.username = username
        user.email = email
        user.save()

        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile')

    return render(request, 'account/profile.html')

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Sua conta foi excluída permanentemente.')
        return redirect('account_login')
    return redirect('profile')

def public_product_list(request):
    products = Product.objects.filter(is_public=True)

    # Search
    q = request.GET.get('q')
    if q:
        products = products.filter(name__icontains=q) | products.filter(description__icontains=q)

    # Price Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Stock Filter
    min_stock = request.GET.get('min_stock')
    max_stock = request.GET.get('max_stock')
    if min_stock:
        products = products.filter(stock__gte=min_stock)
    if max_stock:
        products = products.filter(stock__lte=max_stock)

    products = products.order_by('-created_at')

    return render(request, 'products/product_list.html', {
        'products': products,
        'title': 'Catálogo Público',
        'is_public_view': True,
        'q': q,
        'min_price': min_price,
        'max_price': max_price,
        'min_stock': min_stock,
        'max_stock': max_stock,
    })

def toggle_theme(request):
    current_theme = request.session.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    request.session['theme'] = new_theme
    return redirect(request.META.get('HTTP_REFERER', '/'))

def set_view_mode(request, mode):
    if mode in ['grid', 'table']:
        request.session['view_mode'] = mode
    return redirect(request.META.get('HTTP_REFERER', '/'))
