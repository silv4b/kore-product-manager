from django.contrib import admin

from .models import ExportLog, ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "user", "status", "rows_processed", "rows_failed", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("user", "filename", "created_at", "rows_processed", "rows_failed", "status", "error_details")
    ordering = ("-created_at",)


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "user", "status", "rows_exported", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("user", "filename", "created_at", "rows_exported", "status", "error_details")
    ordering = ("-created_at",)
