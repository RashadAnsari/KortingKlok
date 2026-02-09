from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.test import APIClient

from users.auths import InternalUser, UserTokenAuthentication
from users.models import UserDevice, UserTopicSecret

DEVICE_REGISTRATION_URL = "/api/v1/users/devices"
LOGOUT_URL = "/api/v1/users/logout"


@pytest.fixture
def auth():
    return UserTokenAuthentication()


@pytest.fixture
def request_factory():
    def make_request(authorization=None):
        request = MagicMock()
        request.META = {}
        if authorization is not None:
            request.META["HTTP_AUTHORIZATION"] = authorization
        return request

    return make_request


@pytest.fixture
def user():
    return InternalUser(uid="user123")


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def device_payload():
    return {
        "fcm_token": "fcm-token-abc",
        "device_type": "ios",
        "device_id": "device-001",
        "app_version": "1.0.0",
        "os_version": "18.0",
    }


class TestUserTokenAuthentication:
    def test_missing_header_raises_not_authenticated(self, auth, request_factory):
        with pytest.raises(NotAuthenticated):
            auth.authenticate(request_factory())

    def test_empty_header_raises_not_authenticated(self, auth, request_factory):
        with pytest.raises(NotAuthenticated):
            auth.authenticate(request_factory(authorization=""))

    def test_malformed_header_raises_not_authenticated(self, auth, request_factory):
        with pytest.raises(NotAuthenticated):
            auth.authenticate(request_factory(authorization="Token abc"))

    def test_too_many_parts_raises_not_authenticated(self, auth, request_factory):
        with pytest.raises(NotAuthenticated):
            auth.authenticate(request_factory(authorization="Bearer abc def"))

    @patch("users.auths.auth.verify_id_token", side_effect=ValueError("bad token"))
    def test_invalid_token_raises_authentication_failed(self, mock_verify, auth, request_factory):
        with pytest.raises(AuthenticationFailed):
            auth.authenticate(request_factory(authorization="Bearer bad-token"))

    @patch("users.auths.auth.verify_id_token")
    def test_unverified_email_raises_permission_denied(self, mock_verify, auth, request_factory):
        mock_verify.return_value = {
            "uid": "user123",
            "email_verified": False,
        }
        with pytest.raises(PermissionDenied):
            auth.authenticate(request_factory(authorization="Bearer valid-token"))

    @patch("users.auths.auth.verify_id_token")
    def test_verified_email_returns_user(self, mock_verify, auth, request_factory):
        mock_verify.return_value = {
            "uid": "user123",
            "email_verified": True,
        }
        user, token = auth.authenticate(request_factory(authorization="Bearer valid-token"))
        assert isinstance(user, InternalUser)
        assert user.uid == "user123"
        assert token == "valid-token"

    def test_authenticate_header_returns_bearer(self, auth, request_factory):
        assert auth.authenticate_header(request_factory()) == "Bearer"


@pytest.mark.django_db
class TestGetTopicName:
    def test_creates_topic_secret_on_first_call(self):
        assert not UserTopicSecret.objects.filter(user_id="user123").exists()
        topic = UserTopicSecret.get_topic_name("user123", "nl")
        secret = UserTopicSecret.objects.get(user_id="user123")
        assert topic == f"user_{secret.topic_secret}_user123_nl"

    def test_returns_same_topic_on_subsequent_calls(self):
        topic1 = UserTopicSecret.get_topic_name("user123", "nl")
        topic2 = UserTopicSecret.get_topic_name("user123", "nl")
        assert topic1 == topic2
        assert UserTopicSecret.objects.filter(user_id="user123").count() == 1

    def test_different_language_returns_different_topic(self):
        topic_nl = UserTopicSecret.get_topic_name("user123", "nl")
        topic_en = UserTopicSecret.get_topic_name("user123", "en")
        assert topic_nl != topic_en
        assert topic_nl.endswith("_nl")
        assert topic_en.endswith("_en")
        assert UserTopicSecret.objects.filter(user_id="user123").count() == 1


@pytest.mark.django_db
class TestDeviceRegistration:
    @patch("users.views.messaging.subscribe_to_topic")
    def test_registers_new_device(self, mock_subscribe, api_client, device_payload):
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 204
        device = UserDevice.objects.get(user_id="user123", device_id="device-001")
        assert device.fcm_token == "fcm-token-abc"
        assert device.device_type == "ios"
        assert device.app_version == "1.0.0"
        assert device.os_version == "18.0"
        assert device.language == "nl"

    @patch("users.views.messaging.subscribe_to_topic")
    def test_subscribes_to_user_topic(self, mock_subscribe, api_client, device_payload):
        api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        topic = UserTopicSecret.get_topic_name("user123", "nl")
        mock_subscribe.assert_called_once_with(["fcm-token-abc"], topic)

    @patch("users.views.messaging.subscribe_to_topic")
    def test_updates_existing_device(self, mock_subscribe, api_client, device_payload):
        UserDevice.objects.create(
            user_id="user123",
            device_id="device-001",
            fcm_token="old-token",
            device_type="ios",
        )
        api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert UserDevice.objects.filter(user_id="user123", device_id="device-001").count() == 1
        device = UserDevice.objects.get(user_id="user123", device_id="device-001")
        assert device.fcm_token == "fcm-token-abc"

    @patch("users.views.messaging.subscribe_to_topic")
    def test_registers_with_only_required_fields(self, mock_subscribe, api_client):
        payload = {
            "fcm_token": "fcm-token-abc",
            "device_type": "android",
            "device_id": "device-002",
        }
        response = api_client.post(DEVICE_REGISTRATION_URL, payload, format="json")
        assert response.status_code == 204
        device = UserDevice.objects.get(user_id="user123", device_id="device-002")
        assert device.app_version is None
        assert device.os_version is None

    def test_rejects_missing_required_fields(self, api_client):
        response = api_client.post(DEVICE_REGISTRATION_URL, {}, format="json")
        assert response.status_code == 400

    def test_rejects_invalid_device_type(self, api_client, device_payload):
        device_payload["device_type"] = "windows"
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 400

    @patch("users.views.messaging.subscribe_to_topic")
    def test_registers_device_with_explicit_language(self, mock_subscribe, api_client, device_payload):
        device_payload["language"] = "en"
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 204
        device = UserDevice.objects.get(user_id="user123", device_id="device-001")
        assert device.language == "en"
        topic = UserTopicSecret.get_topic_name("user123", "en")
        mock_subscribe.assert_called_once_with(["fcm-token-abc"], topic)

    @patch("users.views.messaging.unsubscribe_from_topic")
    @patch("users.views.messaging.subscribe_to_topic")
    def test_language_change_switches_topic(self, mock_subscribe, mock_unsubscribe, api_client, device_payload):
        UserDevice.objects.create(
            user_id="user123",
            device_id="device-001",
            fcm_token="fcm-token-abc",
            device_type="ios",
            language="nl",
        )
        device_payload["language"] = "en"
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 204
        old_topic = UserTopicSecret.get_topic_name("user123", "nl")
        new_topic = UserTopicSecret.get_topic_name("user123", "en")
        mock_unsubscribe.assert_called_once_with(["fcm-token-abc"], old_topic)
        mock_subscribe.assert_called_once_with(["fcm-token-abc"], new_topic)
        device = UserDevice.objects.get(user_id="user123", device_id="device-001")
        assert device.language == "en"

    @patch("users.views.messaging.unsubscribe_from_topic")
    @patch("users.views.messaging.subscribe_to_topic")
    def test_same_language_does_not_unsubscribe(self, mock_subscribe, mock_unsubscribe, api_client, device_payload):
        UserDevice.objects.create(
            user_id="user123",
            device_id="device-001",
            fcm_token="old-token",
            device_type="ios",
            language="nl",
        )
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 204
        mock_unsubscribe.assert_not_called()

    def test_rejects_invalid_language(self, api_client, device_payload):
        device_payload["language"] = "fr"
        response = api_client.post(DEVICE_REGISTRATION_URL, device_payload, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogout:
    @patch("users.views.messaging.unsubscribe_from_topic")
    def test_deletes_device_and_unsubscribes(self, mock_unsubscribe, api_client):
        UserDevice.objects.create(
            user_id="user123",
            device_id="device-001",
            fcm_token="fcm-token-abc",
            device_type="ios",
            language="nl",
        )
        topic = UserTopicSecret.get_topic_name("user123", "nl")
        response = api_client.post(LOGOUT_URL, {"device_id": "device-001"}, format="json")
        assert response.status_code == 204
        assert not UserDevice.objects.filter(user_id="user123", device_id="device-001").exists()
        mock_unsubscribe.assert_called_once_with(["fcm-token-abc"], topic)

    @patch("users.views.messaging.unsubscribe_from_topic")
    def test_logout_unsubscribes_from_correct_language_topic(self, mock_unsubscribe, api_client):
        UserDevice.objects.create(
            user_id="user123",
            device_id="device-001",
            fcm_token="fcm-token-abc",
            device_type="ios",
            language="en",
        )
        topic = UserTopicSecret.get_topic_name("user123", "en")
        response = api_client.post(LOGOUT_URL, {"device_id": "device-001"}, format="json")
        assert response.status_code == 204
        mock_unsubscribe.assert_called_once_with(["fcm-token-abc"], topic)

    @patch("users.views.messaging.unsubscribe_from_topic")
    def test_noop_for_nonexistent_device(self, mock_unsubscribe, api_client):
        response = api_client.post(LOGOUT_URL, {"device_id": "no-such-device"}, format="json")
        assert response.status_code == 204
        mock_unsubscribe.assert_not_called()

    def test_rejects_missing_device_id(self, api_client):
        response = api_client.post(LOGOUT_URL, {}, format="json")
        assert response.status_code == 400

    @patch("users.views.messaging.unsubscribe_from_topic")
    def test_only_deletes_own_device(self, mock_unsubscribe, api_client):
        UserDevice.objects.create(
            user_id="other-user",
            device_id="device-001",
            fcm_token="other-token",
            device_type="android",
        )
        response = api_client.post(LOGOUT_URL, {"device_id": "device-001"}, format="json")
        assert response.status_code == 204
        assert UserDevice.objects.filter(user_id="other-user", device_id="device-001").exists()
        mock_unsubscribe.assert_not_called()
