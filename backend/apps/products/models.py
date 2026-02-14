from django.db import models

from utils.models import BaseModelMixin


class Supermarket(BaseModelMixin):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    logo_url = models.TextField(null=True, blank=True)
    website_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "supermarkets"


class Category(BaseModelMixin):
    name = models.CharField(max_length=100)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    supermarket = models.ForeignKey(
        Supermarket,
        on_delete=models.CASCADE,
        related_name="categories",
        related_query_name="category",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="children",
        related_query_name="child",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "categories"
        unique_together = [("supermarket", "external_id")]


class Product(BaseModelMixin):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100)
    image_url = models.TextField(null=True, blank=True)
    website_url = models.TextField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    has_discount = models.BooleanField(default=False)
    discount_text = models.TextField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    supermarket = models.ForeignKey(
        Supermarket,
        on_delete=models.CASCADE,
        related_name="products",
        related_query_name="product",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="products",
        related_query_name="product",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "products"
        unique_together = [("supermarket", "external_id")]
        indexes = [
            models.Index(fields=["supermarket", "is_available"], name="idx_product_supermarket_avail"),
        ]


class PriceHistory(BaseModelMixin):
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    has_discount = models.BooleanField(default=False)
    discount_text = models.TextField(null=True, blank=True)
    run_id = models.UUIDField()
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_histories",
        related_query_name="price_history",
        db_index=True,
    )

    class Meta:
        db_table = "price_history"
        indexes = [
            models.Index(fields=["run_id", "product"], name="idx_price_history_run_product"),
        ]


class UserTrackedProduct(BaseModelMixin):
    user_id = models.CharField(max_length=128)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="tracked_by",
        related_query_name="tracked_product",
    )

    class Meta:
        db_table = "user_tracked_products"
        unique_together = [("user_id", "product")]
