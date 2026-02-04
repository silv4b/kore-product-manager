from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("products/", include("products.urls")),
    path("", include("products.urls")),
    path(
        "__reload__/", include("django_browser_reload.urls")
    ),  # https://github.com/adamchainz/django-browser-reload
]
