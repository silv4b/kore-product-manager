from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.models import Category, Product, ProductMovement

from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductMovementSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar categorias.
    """

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gerenciar produtos.
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_public", "categories"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "stock", "created_at"]

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def movement(self, request, pk=None):
        """
        Registra uma nova movimentação para o produto.
        """
        product = self.get_object()
        serializer = ProductMovementSerializer(data=request.data)

        if serializer.is_valid():
            movement_type = serializer.validated_data["type"]
            quantity = serializer.validated_data["quantity"]

            if movement_type == "OUT" and product.stock < quantity:
                return Response(
                    {"error": "Estoque insuficiente para esta saída."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Salva o movimento
            serializer.save(product=product)

            # Atualiza o estoque do produto manualmente para garantir consistência
            if movement_type == "IN":
                product.stock += quantity
            else:
                product.stock -= quantity
            product.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para visualizar o histórico de movimentações.
    """

    serializer_class = ProductMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "type"]
    ordering_fields = ["moved_at"]

    def get_queryset(self):
        return ProductMovement.objects.filter(product__user=self.request.user)
