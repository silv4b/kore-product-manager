from django.urls import path
from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("detail/<int:pk>/", views.product_detail, name="product_detail"),
    path("public/", views.public_product_list, name="public_product_list"),
    path("add/", views.product_create, name="product_create"),
    path("edit/<int:pk>/", views.product_update, name="product_update"),
    path("delete/<int:pk>/", views.product_delete, name="product_delete"),
    # Categories
    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_create, name="category_create"),
    path("categories/edit/<int:pk>/", views.category_update, name="category_update"),
    path("categories/delete/<int:pk>/", views.category_delete, name="category_delete"),
    path(
        "categories/duplicate/<int:pk>/",
        views.category_duplicate,
        name="category_duplicate",
    ),
    path("profile/", views.profile_view, name="profile"),
    path("profile/delete/", views.delete_account_view, name="delete_account"),
    path("toggle-theme/", views.toggle_theme, name="toggle_theme"),
    path("logout/", views.logout_view, name="custom_logout"),
    path("view-mode/<str:mode>/", views.set_view_mode, name="set_view_mode"),
]
