"""
Rate limiting throttles for Terminal authentication endpoints.

Per FSD §9.1.2: "5 consecutive failures trigger a 15-minute lockout"
Implementation uses DRF's SimpleRateThrottle keyed by IP address.

LoginRateThrottle: 5 requests per 15 minutes (overrides duration to 900s)
RegisterRateThrottle: 5 per hour
PasswordResetRateThrottle: 3 per hour
"""

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """
    Limits login attempts to 5 per 15 minutes per IP.
    Applies to POST /api/v1/auth/login/ only.
    """
    scope = 'auth_login'
    THROTTLE_RATES = {'auth_login': '5/min'}

    def parse_rate(self, rate):
        num_requests, _ = super().parse_rate(rate)
        return (num_requests, 900)

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class RegisterRateThrottle(SimpleRateThrottle):
    """Limits registration to 5 per hour per IP."""
    scope = 'auth_register'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PasswordResetRateThrottle(SimpleRateThrottle):
    """Limits password reset requests to 3 per hour per IP."""
    scope = 'auth_password_reset'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }
