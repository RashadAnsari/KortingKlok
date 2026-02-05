from django.urls import path

from apis.views import HealthAPIView
from rest_framework.routers import SimpleRouter

router = SimpleRouter(trailing_slash=False)

urlpatterns = [
    path("health", HealthAPIView.as_view(), name="health"),
]

urlpatterns = urlpatterns + router.urls
