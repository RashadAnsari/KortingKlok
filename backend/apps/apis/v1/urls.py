from django.urls import path

from apis.views import HealthAPIView
from users.views import DeviceRegistrationAPIView, LogoutAPIView

urlpatterns = [
    path("health", HealthAPIView.as_view(), name="health"),
    path("users/devices", DeviceRegistrationAPIView.as_view(), name="device-registration"),
    path("users/logout", LogoutAPIView.as_view(), name="logout"),
]
