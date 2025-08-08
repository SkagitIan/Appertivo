from django.utils.deprecation import MiddlewareMixin
from .models import UserProfile
import uuid

class AnonymousTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.headers.get('X-Anonymous-Token') or request.COOKIES.get('anonymous_token')
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
            except UserProfile.DoesNotExist:
                user_profile = UserProfile.objects.create(anonymous_token=token_uuid)
            except ValueError:
                user_profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())
        else:
            user_profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())

        request.user_profile = user_profile

    def process_response(self, request, response):
        if hasattr(request, 'user_profile') and request.user_profile.anonymous_token:
            response.set_cookie('anonymous_token', str(request.user_profile.anonymous_token), max_age=60*60*24*365)
            response['X-User-Profile'] = str(request.user_profile)
        return response
