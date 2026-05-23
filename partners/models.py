from django.contrib.auth.models import User
from django.db import models


class Partner(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="%(class)s_set")
    name = models.CharField(max_length=255, verbose_name="Nome")
    email = models.EmailField(blank=True, default="", verbose_name="E-mail")
    phone = models.CharField(max_length=20, blank=True, default="", verbose_name="Telefone")
    street = models.CharField(max_length=255, blank=True, default="", verbose_name="Logradouro")
    number = models.CharField(max_length=20, blank=True, default="", verbose_name="Número")
    complement = models.CharField(max_length=100, blank=True, default="", verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, blank=True, default="", verbose_name="Bairro")
    city = models.CharField(max_length=100, blank=True, default="", verbose_name="Cidade")
    state = models.CharField(max_length=2, blank=True, default="", verbose_name="UF")
    zip_code = models.CharField(max_length=10, blank=True, default="", verbose_name="CEP")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True

    @property
    def full_address(self):
        parts = [self.street, self.number, self.complement, self.neighborhood, self.city, self.state, self.zip_code]
        return ", ".join(p for p in parts if p) or ""


class Customer(Partner):
    cpf = models.CharField(max_length=14, blank=True, default="", verbose_name="CPF")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def __str__(self):
        return f"Cliente: {self.name}"


class Supplier(Partner):
    class RegimeTributarioChoices(models.TextChoices):
        SIMPLES_NACIONAL = "SIMPLES_NACIONAL", "Simples Nacional"
        LUCRO_PRESUMIDO = "LUCRO_PRESUMIDO", "Lucro Presumido"
        LUCRO_REAL = "LUCRO_REAL", "Lucro Real"

    class StatusChoices(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        BLOQUEADO = "bloqueado", "Bloqueado"

    cnpj = models.CharField(max_length=18, blank=True, default="", verbose_name="CNPJ")
    company_name = models.CharField(max_length=255, blank=True, default="", verbose_name="Razão Social")
    contact_person = models.CharField(max_length=255, blank=True, default="", verbose_name="Pessoa de Contato")
    website = models.URLField(blank=True, default="", verbose_name="Website")
    observations = models.TextField(blank=True, default="", verbose_name="Observações")
    inscricao_estadual = models.CharField(max_length=20, blank=True, default="", verbose_name="Inscrição Estadual")
    inscricao_municipal = models.CharField(max_length=20, blank=True, default="", verbose_name="Inscrição Municipal")
    regime_tributario = models.CharField(
        max_length=20, choices=RegimeTributarioChoices.choices, blank=True, default="", verbose_name="Regime Tributário"
    )
    prazo_entrega_medio = models.PositiveIntegerField(null=True, blank=True, verbose_name="Prazo de Entrega Médio (dias)")
    condicoes_pagamento_padrao = models.CharField(max_length=100, blank=True, default="", verbose_name="Condições de Pagamento")
    status = models.CharField(max_length=10, choices=StatusChoices.choices, blank=True, default=StatusChoices.ATIVO, verbose_name="Status")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]

    def __str__(self):
        return f"Fornecedor: {self.name}"
