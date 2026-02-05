from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apis.serializers import ErrorResponseSerializer


def api_success(data=None, status_code: int = status.HTTP_200_OK) -> Response:
    return Response(data=data, status=status_code if data else status.HTTP_204_NO_CONTENT)


class HealthAPIView(APIView):
    throttle_classes = []
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        tags=["Health"],
        responses={204: None, 500: ErrorResponseSerializer},
    )
    def get(self, request):
        return api_success()
