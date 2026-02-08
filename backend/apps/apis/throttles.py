from rest_framework.throttling import SimpleRateThrottle


class AnonRateThrottle(SimpleRateThrottle):
    scope = "anon"

    def get_cache_key(self, request, view):
        if request.user:
            return None  # Only throttle unauthenticated requests

        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class UserRateThrottle(SimpleRateThrottle):
    scope = "user"

    def get_cache_key(self, request, view):
        if request.user:
            ident = request.user.uid
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
