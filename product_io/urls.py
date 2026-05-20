from django.urls import path

from . import views

app_name = "product_io"

urlpatterns = [
    path("export/", views.ProductExportView.as_view(), name="product_export"),
    path("import/", views.ProductImportView.as_view(), name="product_import"),
]
