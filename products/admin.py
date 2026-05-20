from django.contrib import admin
from django.utils.html import format_html

from .models import Category, PriceHistory, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "price", "cost_price", "profit_margin_display", "stock",
        "min_stock_level", "stock_status", "supplier", "is_public", "user", "created_at"
    ]
    list_filter = ["is_public", "categories", "created_at", "supplier"]
    search_fields = ["name", "description"]

    def profit_margin_display(self, obj):
        return f"{obj.profit_margin:.2f}%"
    profit_margin_display.short_description = "Margem de Lucro"

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color: #dc2626; font-weight: bold;">Crítico</span>')
        return format_html('<span style="color: #16a34a;">Normal</span>')
    stock_status.short_description = "Status Estoque"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "color"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ["product", "price", "changed_at"]
    list_filter = ["changed_at"]
    search_fields = ["product__name"]
    readonly_fields = ["product", "price", "changed_at"]

    def has_add_permission(self, request):
        # Previne criação manual - apenas via signal
        return False
