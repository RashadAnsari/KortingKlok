from rest_framework import serializers

from products.models import Category, Product, Supermarket


class SupermarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supermarket
        fields = ["id", "name", "slug", "logo_url", "website_url"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    is_tracked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "supermarket",
            "category",
            "base_price",
            "current_price",
            "has_discount",
            "discount_text",
            "image_url",
            "website_url",
            "is_tracked",
        ]

    def get_is_tracked(self, obj) -> bool:
        return getattr(obj, "is_tracked", False)


class PaginatedProductSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ProductSerializer(many=True)


class CategoryFilterSerializer(serializers.Serializer):
    supermarket = serializers.IntegerField(required=False)
    parent = serializers.IntegerField(required=False)


class ProductSearchFilterSerializer(serializers.Serializer):
    q = serializers.CharField(required=False)
    supermarket = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)


class DealFilterSerializer(serializers.Serializer):
    supermarket = serializers.IntegerField(required=False)
