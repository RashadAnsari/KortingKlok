from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied

from apis.auths import FirebaseUser, UserTokenAuthentication


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

    @patch("apis.auths.auth.verify_id_token", side_effect=ValueError("bad token"))
    def test_invalid_token_raises_authentication_failed(self, mock_verify, auth, request_factory):
        with pytest.raises(AuthenticationFailed):
            auth.authenticate(request_factory(authorization="Bearer bad-token"))

    @patch("apis.auths.auth.verify_id_token")
    def test_unverified_email_raises_permission_denied(self, mock_verify, auth, request_factory):
        mock_verify.return_value = {
            "uid": "user123",
            "email_verified": False,
        }
        with pytest.raises(PermissionDenied):
            auth.authenticate(request_factory(authorization="Bearer valid-token"))

    @patch("apis.auths.auth.verify_id_token")
    def test_verified_email_returns_user(self, mock_verify, auth, request_factory):
        mock_verify.return_value = {
            "uid": "user123",
            "email_verified": True,
        }
        user, token = auth.authenticate(request_factory(authorization="Bearer valid-token"))
        assert isinstance(user, FirebaseUser)
        assert user.uid == "user123"
        assert token == "valid-token"

    def test_authenticate_header_returns_bearer(self, auth, request_factory):
        assert auth.authenticate_header(request_factory()) == "Bearer"
