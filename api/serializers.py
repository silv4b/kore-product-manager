from django.contrib.auth.models import User
from rest_framework import serializers

from products.models import Category, PriceHistory, Product, ProductMovement, Supplier


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact", "observations", "created_at"]
        read_only_fields = ["user", "created_at"]


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

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("A quantidade deve ser maior que zero.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Category.objects.none(),
        source="categories",
        required=False,
    )
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.none(),
        source="supplier",
        required=False,
        allow_null=True,
        write_only=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            self.fields["category_ids"].queryset = Category.objects.filter(user=request.user)
            if hasattr(self.fields["category_ids"], "child_relation"):
                self.fields["category_ids"].child_relation.queryset = Category.objects.filter(user=request.user)
            self.fields["supplier_id"].queryset = Supplier.objects.filter(user=request.user)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "cost_price",
            "min_stock_level",
            "profit_margin",
            "stock",
            "is_public",
            "created_at",
            "updated_at",
            "categories",
            "category_ids",
            "supplier",
            "supplier_id",
        ]
        read_only_fields = ["user", "created_at", "updated_at", "profit_margin"]


class ProductDetailSerializer(ProductSerializer):
    price_history = PriceHistorySerializer(many=True, read_only=True)
    movements = ProductMovementSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["price_history", "movements"]
