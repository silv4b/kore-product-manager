from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerForm, SupplierForm
from .models import Customer, Supplier


@login_required
def partner_list(request):
    """View principal para listar ambos"""
    customers = Customer.objects.filter(user=request.user)
    suppliers = Supplier.objects.filter(user=request.user)
    return render(
        request,
        "partners/partner_list.html",
        {
            "customers": customers,
            "suppliers": suppliers,
            "title": "Clientes & Fornecedores",
        },
    )


# --- Customer Views ---
@login_required
def customer_list(request):
    sort_field = request.GET.get("sort", "name")
    sort_direction = request.GET.get("dir", "asc")

    valid_sort_fields = {
        "name": "name",
        "email": "email",
        "phone": "phone",
        "cpf": "cpf",
        "birth_date": "birth_date",
    }

    target_field = valid_sort_fields.get(sort_field, "name")
    prefix = "" if sort_direction == "asc" else "-"

    customers = Customer.objects.filter(user=request.user).order_by(
        f"{prefix}{target_field}"
    )

    return render(
        request,
        "partners/customer_list.html",
        {"customers": customers, "title": "Meus Clientes"},
    )


@login_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.user = request.user
            customer.save()
            messages.success(request, f'Cliente "{customer.name}" criado com sucesso!')
            return redirect("customer_list")
    else:
        form = CustomerForm()
    return render(
        request,
        "partners/partner_form.html",
        {"form": form, "title": "Novo Cliente", "type": "customer"},
    )


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk, user=request.user)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Cliente "{customer.name}" atualizado com sucesso!'
            )
            return redirect("customer_list")
    else:
        form = CustomerForm(instance=customer)
    return render(
        request,
        "partners/partner_form.html",
        {
            "form": form,
            "title": "Editar Cliente",
            "type": "customer",
            "object": customer,
        },
    )


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, user=request.user)
    if request.method == "POST":
        name = customer.name
        customer.delete()
        messages.success(request, f'Cliente "{name}" removido.')
        return redirect("customer_list")
    return render(
        request,
        "partners/partner_confirm_delete.html",
        {"object": customer, "type": "cliente"},
    )


# --- Supplier Views ---
@login_required
def supplier_list(request):
    sort_field = request.GET.get("sort", "name")
    sort_direction = request.GET.get("dir", "asc")

    valid_sort_fields = {
        "name": "name",
        "company_name": "company_name",
        "cnpj": "cnpj",
        "email": "email",
        "phone": "phone",
        "contact_person": "contact_person",
    }

    target_field = valid_sort_fields.get(sort_field, "name")
    prefix = "" if sort_direction == "asc" else "-"

    suppliers = Supplier.objects.filter(user=request.user).order_by(
        f"{prefix}{target_field}"
    )

    return render(
        request,
        "partners/supplier_list.html",
        {"suppliers": suppliers, "title": "Meus Fornecedores"},
    )


@login_required
def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.user = request.user
            supplier.save()
            messages.success(
                request, f'Fornecedor "{supplier.name}" criado com sucesso!'
            )
            return redirect("supplier_list")
    else:
        form = SupplierForm()
    return render(
        request,
        "partners/partner_form.html",
        {"form": form, "title": "Novo Fornecedor", "type": "supplier"},
    )


@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, user=request.user)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Fornecedor "{supplier.name}" atualizado com sucesso!'
            )
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=supplier)
    return render(
        request,
        "partners/partner_form.html",
        {
            "form": form,
            "title": "Editar Fornecedor",
            "type": "supplier",
            "object": supplier,
        },
    )


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, user=request.user)
    if request.method == "POST":
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Fornecedor "{name}" removido.')
        return redirect("supplier_list")
    return render(
        request,
        "partners/partner_confirm_delete.html",
        {"object": supplier, "type": "fornecedor"},
    )
