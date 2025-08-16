"""Middleware for attaching a ``UserProfile`` to incoming requests."""

import uuid

from django.utils.deprecation import MiddlewareMixin

from .models import UserProfile

class AnonymousTokenMiddleware(MiddlewareMixin):
    """Attach a ``UserProfile`` based on user authentication or anonymous token.

    A new anonymous profile is created only when the user enters the
    special-creation flow (URLs beginning with ``/specials/``). Existing
    tokens are reused regardless of the path.
    """

    special_prefixes = ("/specials/",)

    def _in_special_flow(self, path: str) -> bool:
        """Return ``True`` if the request path is part of the special flow."""

        return any(path.startswith(prefix) for prefix in self.special_prefixes)

    def process_request(self, request):
        token = request.headers.get("X-Anonymous-Token") or request.COOKIES.get(
            "anonymous_token"
        )
        user_profile = None

        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                user_profile = UserProfile.objects.create(user=request.user)
        elif token:
            try:
                token_uuid = uuid.UUID(token)
                user_profile = UserProfile.objects.get(anonymous_token=token_uuid)
            except (UserProfile.DoesNotExist, ValueError):
                if self._in_special_flow(request.path):
                    user_profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())
        elif self._in_special_flow(request.path):
            user_profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())

        request.user_profile = user_profile

    def process_response(self, request, response):
        profile = getattr(request, "user_profile", None)
        if profile and profile.anonymous_token:
            response.set_cookie(
                "anonymous_token",
                str(profile.anonymous_token),
                max_age=60 * 60 * 24 * 365,
            )
            response["X-User-Profile"] = str(profile)
        return response
