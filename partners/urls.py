from django.urls import path

from . import views

urlpatterns = [
    path("", views.partner_list, name="partner_list"),
    # Customers
    path("clientes/", views.customer_list, name="customer_list"),
    path("clientes/novo/", views.customer_create, name="customer_create"),
    path("clientes/<int:pk>/editar/", views.customer_update, name="customer_update"),
    path("clientes/<int:pk>/excluir/", views.customer_delete, name="customer_delete"),
    # Suppliers
    path("fornecedores/", views.supplier_list, name="partner_supplier_list"),
    path("fornecedores/novo/", views.supplier_create, name="partner_supplier_create"),
    path(
        "fornecedores/<int:pk>/editar/", views.supplier_update, name="partner_supplier_update"
    ),
    path(
        "fornecedores/<int:pk>/excluir/", views.supplier_delete, name="partner_supplier_delete"
    ),
]
