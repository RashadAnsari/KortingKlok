import uuid

from django.db import models

from utils.models import BaseModelMixin


class UserTopicSecret(BaseModelMixin):
    user_id = models.CharField(max_length=128, primary_key=True)
    topic_secret = models.UUIDField(default=uuid.uuid4)

    class Meta:
        db_table = "user_topic_secrets"

    @classmethod
    def get_topic_name(cls, user_id: str, language: str) -> str:
        secret, _ = cls.objects.get_or_create(user_id=user_id)
        return f"user_{secret.topic_secret}_{user_id}_{language}"


class DeviceType(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class Language(models.TextChoices):
    NL = "nl", "Nederlands"
    EN = "en", "English"


class UserDevice(BaseModelMixin):
    user_id = models.CharField(max_length=128, db_index=True)
    fcm_token = models.TextField(unique=True)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    device_name = models.CharField(max_length=100, null=True, blank=True)
    device_id = models.CharField(max_length=255)
    app_version = models.CharField(max_length=20, null=True, blank=True)
    os_version = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.NL)

    class Meta:
        db_table = "user_devices"
        unique_together = [("user_id", "device_id")]
