from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("products/", include("products.urls")),
    path("products/io/", include("product_io.urls")),
    path("partners/", include("partners.urls")),
    path("api/v1/", include("api.urls")),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.BASE_DIR / "static",
    )
