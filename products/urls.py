from django.urls import path

from . import views

urlpatterns = [
    # Product Core
    path("", views.ProductListView.as_view(), name="product_list"),
    path("detail/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("price-history/<int:pk>/", views.PriceHistoryView.as_view(), name="price_history"),
    path("price-history/", views.PriceHistoryOverviewView.as_view(), name="price_history_overview"),
    path("movements/<int:pk>/", views.ProductMovementView.as_view(), name="product_movement"),
    path("movements/", views.ProductMovementOverviewView.as_view(), name="product_movement_overview"),
    path("movements/select/<str:type>/", views.MovementSelectProductView.as_view(), name="movement_select_product"),
    path("movements/perform/<int:pk>/<str:type>/", views.PerformMovementView.as_view(), name="perform_movement"),
    path("public/", views.PublicProductListView.as_view(), name="public_product_list"),
    path("add/", views.ProductCreateView.as_view(), name="product_create"),
    path("edit/<int:pk>/", views.ProductUpdateView.as_view(), name="product_update"),
    path("delete/<int:pk>/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("bulk-action/", views.ProductBulkActionView.as_view(), name="product_bulk_action"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/edit/<int:pk>/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/delete/<int:pk>/", views.CategoryDeleteView.as_view(), name="category_delete"),
    path("categories/duplicate/<int:pk>/", views.CategoryDuplicateView.as_view(), name="category_duplicate"),

    # Suppliers
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/add/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("suppliers/edit/<int:pk>/", views.SupplierUpdateView.as_view(), name="supplier_update"),
    path("suppliers/delete/<int:pk>/", views.SupplierDeleteView.as_view(), name="supplier_delete"),

    # Reports
    path("reports/", views.ReportDashboardView.as_view(), name="report_dashboard"),

    # Profile & System
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/delete/", views.DeleteAccountView.as_view(), name="delete_account"),
    path("catalog/<str:username>/", views.UserPublicCatalogView.as_view(), name="user_public_catalog"),
    path("toggle-theme/", views.ToggleThemeView.as_view(), name="toggle_theme"),
    path("logout/", views.CustomLogoutView.as_view(), name="custom_logout"),
    path("view-mode/<str:context>/<str:mode>/", views.SetViewModeView.as_view(), name="set_view_mode"),
]
