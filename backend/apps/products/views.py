from django.db.models import Exists, OuterRef

from apis.serializers import ErrorResponseSerializer
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Category, Product, Supermarket, UserTrackedProduct
from products.serializers import (
    CategoryFilterSerializer,
    CategorySerializer,
    PaginatedProductSerializer,
    ProductSearchFilterSerializer,
    ProductSerializer,
    SupermarketSerializer,
)


class _ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SupermarketListAPIView(APIView):
    @extend_schema(
        tags=["Products"],
        responses={
            200: SupermarketSerializer(many=True),
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        supermarkets = Supermarket.objects.all().order_by("id")
        return Response(SupermarketSerializer(supermarkets, many=True).data)


class CategoryListAPIView(APIView):
    @extend_schema(
        tags=["Products"],
        parameters=[
            OpenApiParameter("supermarket", int, description="Supermarket ID"),
            OpenApiParameter("parent", int, description="Parent category ID (omit for root categories)"),
        ],
        responses={
            200: CategorySerializer(many=True),
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        filters = CategoryFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        params = filters.validated_data

        qs = Category.objects.all().order_by("name")

        if "supermarket" in params:
            qs = qs.filter(supermarket_id=params["supermarket"])

        if "parent" in params:
            qs = qs.filter(parent_id=params["parent"])
        else:
            qs = qs.filter(parent__isnull=True)

        return Response(CategorySerializer(qs, many=True).data)


class ProductSearchAPIView(APIView):
    @extend_schema(
        tags=["Products"],
        parameters=[
            OpenApiParameter("q", str, description="Search query"),
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("category", int, description="Category ID"),
            OpenApiParameter("supermarket", int, description="Supermarket ID"),
            OpenApiParameter("page_size", int, description="Results per page (max 100)"),
        ],
        responses={
            200: PaginatedProductSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def get(self, request):
        filters = ProductSearchFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        params = filters.validated_data

        qs = (
            Product.objects.filter(is_available=True)
            .select_related("category")
            .annotate(
                is_tracked=Exists(
                    UserTrackedProduct.objects.filter(
                        user_id=request.user.uid,
                        product_id=OuterRef("pk"),
                    )
                )
            )
        )

        if "q" in params:
            qs = qs.filter(name__icontains=params["q"])

        if "supermarket" in params:
            qs = qs.filter(supermarket_id=params["supermarket"])

        if "category" in params:
            qs = qs.filter(category_id=params["category"])

        qs = qs.order_by("-has_discount", "name")

        paginator = _ProductPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ProductSerializer(page, many=True).data)


class ProductTrackingAPIView(APIView):
    @extend_schema(
        tags=["Products"],
        request=None,
        responses={
            204: None,
            404: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id {product_id} not found.")
        UserTrackedProduct.objects.get_or_create(user_id=request.user.uid, product=product)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Products"],
        request=None,
        responses={
            204: None,
            404: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id {product_id} not found.")
        UserTrackedProduct.objects.filter(user_id=request.user.uid, product=product).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
