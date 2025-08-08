import uuid
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from .models import UserProfile
from .forms import SignUpForm, EmailAuthenticationForm
from app.models import Special

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


class EmailLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = "registration/login.html"

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        if not remember:
            self.request.session.set_expiry(0)
        return super().form_valid(form)


def signup(request):
    profile = getattr(request, "user_profile", None)
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if profile:
                profile.user = user
                profile.email = user.email
                profile.save()
            return redirect("profile")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user_profile
    today = timezone.localdate()
    active_specials = Special.objects.filter(
        user_profile=profile,
        published=True,
    ).filter(Q(end_date__gte=today) | Q(end_date__isnull=True))
    expired_specials = Special.objects.filter(
        user_profile=profile,
        published=True,
        end_date__lt=today,
    )
    email_signups = profile.email_signups.order_by("-created_at")
    embed_code = f'<script src="{request.build_absolute_uri(reverse("appertivo_widget"))}?restaurant={profile.id}"></script>'
    return render(
        request,
        "profiles/profile.html",
        {
            "active_specials": active_specials,
            "expired_specials": expired_specials,
            "email_signups": email_signups,
            "embed_code": embed_code,
        },
    )
