from django.urls import include, path

# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("v1/", include("apis.v1.urls")),
    # path("swagger-schema", SpectacularAPIView.as_view(), name="schema"),
    # path("swagger-ui", SpectacularSwaggerView.as_view(), name="swagger-ui"),
]
