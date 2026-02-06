from dataclasses import dataclass

from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied


@dataclass
class FirebaseUser:
    uid: str


class UserTokenAuthentication(BaseAuthentication):
    bearer = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "").split()
        if not header or len(header) != 2 or header[0].lower() != self.bearer.lower():
            raise NotAuthenticated()

        token = header[1]
        try:
            decoded = auth.verify_id_token(token, check_revoked=True)
        except Exception:
            raise AuthenticationFailed()

        if not decoded.get("email_verified", False):
            raise PermissionDenied()

        user = FirebaseUser(uid=decoded["uid"])
        return (user, token)

    def authenticate_header(self, request):
        return self.bearer
