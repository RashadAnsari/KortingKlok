from dataclasses import dataclass

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated


@dataclass
class InternalUser:
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

        user = InternalUser(uid=decoded["uid"])
        return (user, token)

    def authenticate_header(self, request):
        return self.bearer


class UserTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    name = "bearerAuth"
    target_class = "users.auths.UserTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
