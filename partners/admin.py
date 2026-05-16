from django.contrib import admin

from .models import Customer, Supplier


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "cpf", "user")
    search_fields = ("name", "email", "cpf")
    list_filter = ("user",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "company_name", "cnpj", "email", "user")
    search_fields = ("name", "company_name", "cnpj")
    list_filter = ("user",)
