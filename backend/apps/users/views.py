from django.db import transaction

from apis.serializers import ErrorResponseSerializer
from drf_spectacular.utils import extend_schema
from firebase_admin import messaging
from rest_framework import status
from rest_framework.response import Response
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
        language = request_data["language"]
        device_id = request_data["device_id"]

        # Check if device exists with a different language to handle topic switch
        old_device = UserDevice.objects.filter(
            user_id=user_id,
            device_id=device_id,
        ).first()

        if old_device and old_device.language != language:
            old_topic = UserTopicSecret.get_topic_name(user_id, old_device.language)
            messaging.unsubscribe_from_topic([old_device.fcm_token], old_topic)

        UserDevice.objects.update_or_create(
            user_id=user_id,
            device_id=device_id,
            defaults={
                "fcm_token": fcm_token,
                "device_type": request_data["device_type"],
                "app_version": request_data.get("app_version"),
                "os_version": request_data.get("os_version"),
                "language": language,
            },
        )

        topic = UserTopicSecret.get_topic_name(user_id, language)
        messaging.subscribe_to_topic([fcm_token], topic)

        return Response(status=status.HTTP_204_NO_CONTENT)


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
            topic = UserTopicSecret.get_topic_name(user_id, device.language)
            messaging.unsubscribe_from_topic([device.fcm_token], topic)
            device.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
