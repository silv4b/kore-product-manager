from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class ImportLog(models.Model):
    """Registra cada operação de importação de CSV."""

    STATUS_CHOICES = [
        ("SUCCESS", "Sucesso"),
        ("PARTIAL", "Parcial"),
        ("FAILED", "Falha"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_import_logs",
    )
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    rows_processed = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_details = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log de Importação"
        verbose_name_plural = "Logs de Importação"

    def __str__(self):
        return f"Import {self.filename} - {self.status} ({self.created_at:%d/%m/%Y %H:%M})"


class ExportLog(models.Model):
    """Registra cada operação de exportação de CSV."""

    STATUS_CHOICES = [
        ("SUCCESS", "Sucesso"),
        ("FAILED", "Falha"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_export_logs",
    )
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    rows_exported = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_details = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log de Exportação"
        verbose_name_plural = "Logs de Exportação"

    def __str__(self):
        return f"Export {self.filename} - {self.status} ({self.created_at:%d/%m/%Y %H:%M})"
