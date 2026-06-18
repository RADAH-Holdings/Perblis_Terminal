"""Search throttle: 60/min anonymous, 120/min authenticated (TSD §3.8).

A single endpoint serves guests and signed-in hirers, so the scope is chosen
per-request by auth state rather than fixed on the view. Rates live in
``REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`` (``search_anon`` / ``auth``).
"""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class SearchRateThrottle(SimpleRateThrottle):
    scope = "search_anon"  # default; recomputed per-request in allow_request

    def __init__(self):
        # Rate is resolved per-request (scope depends on auth), not at init.
        pass

    def allow_request(self, request, view):
        authed = bool(request.user and request.user.is_authenticated)
        self.scope = "auth" if authed else "search_anon"
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)

    def get_cache_key(self, request, view) -> str:
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
