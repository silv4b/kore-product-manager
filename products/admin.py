from django.contrib import admin

from .models import Category, PriceHistory, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "stock", "is_public", "user", "created_at"]
    list_filter = ["is_public", "categories", "created_at"]
    search_fields = ["name", "description"]


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
