import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import UserProfile
import uuid

@csrf_exempt
def create_or_update_profile(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    token = request.headers.get('X-Anonymous-Token')
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    if token:
        try:
            profile = UserProfile.objects.get(anonymous_token=uuid.UUID(token))
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())
    else:
        profile = UserProfile.objects.create(anonymous_token=uuid.uuid4())

    website = data.get('website')
    email = data.get('email')
    business_name = data.get('business_name')
    phone = data.get('phone')

    if website:
        profile.website = website
    if email:
        profile.email = email
    if business_name:
        profile.business_name = business_name
    if phone:
        profile.phone = phone

    profile.save()

    response_data = {
        "anonymous_token": str(profile.anonymous_token),
        "email": profile.email,
        "business_name": profile.business_name,
        "website": profile.website,
        "phone": profile.phone,
        "is_premium": profile.is_premium,
    }
    return JsonResponse(response_data)
