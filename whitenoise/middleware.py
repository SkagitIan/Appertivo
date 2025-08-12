"""Minimal stub middleware used for tests when whitenoise isn't installed."""

class WhiteNoiseMiddleware:
    """Pass-through middleware stub."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
