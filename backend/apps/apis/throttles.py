from rest_framework.throttling import SimpleRateThrottle


class RateLimiter(SimpleRateThrottle):
    scope = "rate_limiter"

    def get_cache_key(self, request, view):
        ident = request.user.uid if request.user else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
