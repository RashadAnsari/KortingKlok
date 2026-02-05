from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import OpenApiParameter


class UserTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    name = "bearerAuth"
    target_class = "apps.apis.auths.UserTokenAuthentication"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


def get_schema_parameters(params: list[str]) -> list[OpenApiParameter]:
    params_map = {
        "offset": OpenApiParameter(name="offset", location="query", type=int, default=0),
        "limit": OpenApiParameter(name="limit", location="query", type=int, default=20),
    }

    return [params_map[param] for param in params]
