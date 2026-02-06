from rest_framework import serializers

from users.models import DeviceType, Language


class DeviceRegistrationSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()
    device_type = serializers.ChoiceField(choices=DeviceType.choices)
    device_id = serializers.CharField(max_length=255)
    device_name = serializers.CharField(max_length=100, required=False)
    app_version = serializers.CharField(max_length=20, required=False)
    os_version = serializers.CharField(max_length=50, required=False)
    language = serializers.ChoiceField(choices=Language.choices, default=Language.NL)


class LogoutSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=255)
