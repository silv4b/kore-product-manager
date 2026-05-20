from django.contrib.auth.models import User
from django.db import models


class Partner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_set")
    name = models.CharField(max_length=255, verbose_name="Nome")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True


class Customer(Partner):
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def __str__(self):
        return f"Cliente: {self.name}"


class Supplier(Partner):
    cnpj = models.CharField(max_length=18, blank=True, null=True, verbose_name="CNPJ")
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razão Social")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="Pessoa de Contato")
    website = models.URLField(blank=True, null=True, verbose_name="Website")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]

    def __str__(self):
        return f"Fornecedor: {self.name}"
