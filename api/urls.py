from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

router = DefaultRouter()
router.register(r"storage-locations", views.StorageLocationViewSet, basename="storage_location")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"suppliers", views.SupplierViewSet, basename="supplier")
router.register(r"products", views.ProductViewSet, basename="product")
router.register(r"movements", views.ProductMovementViewSet, basename="movement")
router.register(r"stocks", views.StockViewSet, basename="stock")

urlpatterns = [
    path("", include(router.urls)),
    # Autenticação JWT
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Documentação
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
