import uuid

from django.db import models

from apps.utils.models import BaseModelMixin


class UserTopicSecret(BaseModelMixin):
    user_id = models.CharField(max_length=128, primary_key=True)
    topic_secret = models.UUIDField(default=uuid.uuid4)

    class Meta:
        db_table = "user_topic_secrets"


class DeviceType(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class UserDevice(BaseModelMixin):
    user_id = models.CharField(max_length=128, db_index=True)
    fcm_token = models.TextField(unique=True)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    device_name = models.CharField(max_length=100, null=True, blank=True)
    device_id = models.CharField(max_length=255)
    app_version = models.CharField(max_length=20, null=True, blank=True)
    os_version = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "user_devices"
        unique_together = [("user_id", "device_id")]
