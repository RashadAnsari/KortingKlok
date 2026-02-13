from django.urls import path

from apis.views import HealthAPIView
from products.views import (
    CategoryListAPIView,
    DealListAPIView,
    ProductSearchAPIView,
    ProductTrackingAPIView,
    SupermarketListAPIView,
)
from users.views import DeviceRegistrationAPIView, LogoutAPIView

urlpatterns = [
    path("health", HealthAPIView.as_view(), name="health"),
    path("users/devices", DeviceRegistrationAPIView.as_view(), name="device-registration"),
    path("users/logout", LogoutAPIView.as_view(), name="logout"),
    path("products/supermarkets", SupermarketListAPIView.as_view(), name="supermarket-list"),
    path("products/categories", CategoryListAPIView.as_view(), name="category-list"),
    path("products/search", ProductSearchAPIView.as_view(), name="product-search"),
    path("products/deals", DealListAPIView.as_view(), name="deal-list"),
    path("products/<int:product_id>/track", ProductTrackingAPIView.as_view(), name="product-track"),
]
