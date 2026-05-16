from django.contrib.auth.models import User
from rest_framework import serializers

from products.models import Category, PriceHistory, Product, ProductMovement


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "color"]
        read_only_fields = ["user"]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ["id", "price", "changed_at"]


class ProductMovementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ProductMovement
        fields = [
            "id",
            "product",
            "type",
            "type_display",
            "quantity",
            "reason",
            "moved_at",
        ]
        read_only_fields = ["product", "moved_at"]


class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Category.objects.all(),
        source="categories",
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "is_public",
            "created_at",
            "updated_at",
            "categories",
            "category_ids",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class ProductDetailSerializer(ProductSerializer):
    price_history = PriceHistorySerializer(many=True, read_only=True)
    movements = ProductMovementSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["price_history", "movements"]
