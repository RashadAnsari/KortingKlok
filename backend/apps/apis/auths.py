from rest_framework.authentication import BaseAuthentication


class UserTokenAuthentication(BaseAuthentication):
    bearer = "Bearer"

    def authenticate(self, request):
        return (None, None)

    def authenticate_header(self, request):
        return self.bearer
