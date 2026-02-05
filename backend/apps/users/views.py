from django.db import transaction

from apis.serializers import ErrorResponseSerializer
from apis.views import api_success
from drf_spectacular.utils import extend_schema
from firebase_admin import messaging
from rest_framework.views import APIView

from users.models import UserDevice, UserTopicSecret
from users.serializers import DeviceRegistrationSerializer, LogoutSerializer


class DeviceRegistrationAPIView(APIView):
    @extend_schema(
        tags=["Users"],
        request=DeviceRegistrationSerializer,
        responses={
            204: None,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    @transaction.atomic
    def post(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data

        user_id = request.user.uid
        fcm_token = request_data["fcm_token"]

        UserDevice.objects.update_or_create(
            user_id=user_id,
            device_id=request_data["device_id"],
            defaults={
                "fcm_token": fcm_token,
                "device_type": request_data["device_type"],
                "device_name": request_data.get("device_name"),
                "app_version": request_data.get("app_version"),
                "os_version": request_data.get("os_version"),
            },
        )

        topic = UserTopicSecret.get_topic_name(user_id)
        messaging.subscribe_to_topic([fcm_token], topic)

        return api_success()


class LogoutAPIView(APIView):
    @extend_schema(
        tags=["Users"],
        request=LogoutSerializer,
        responses={
            204: None,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    @transaction.atomic
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_data = serializer.validated_data

        user_id = request.user.uid
        device = UserDevice.objects.filter(
            user_id=user_id,
            device_id=request_data["device_id"],
        ).first()

        if device:
            topic = UserTopicSecret.get_topic_name(user_id)
            messaging.unsubscribe_from_topic([device.fcm_token], topic)
            device.delete()

        return api_success()
