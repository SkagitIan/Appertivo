from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.contrib.auth.tokens import default_token_generator
from .models import UserProfile
from .forms import SignUpForm, EmailAuthenticationForm
from app.models import Special
from .emails import send_verification_email
from django.contrib.auth import login, authenticate
# app/views_auth.py
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
User = get_user_model()
from django.shortcuts import get_object_or_404, render

class EmailLoginView(LoginView):
    form_class = EmailAuthenticationForm
    template_name = "registration/login.html"

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        if not remember:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to `next` if provided and safe."""
        redirect_to = self.request.POST.get(self.redirect_field_name) or self.request.GET.get(
            self.redirect_field_name
        )
        if redirect_to and url_has_allowed_host_and_scheme(
            redirect_to, allowed_hosts={self.request.get_host()}
        ):
            return redirect_to
        return super().get_success_url()



def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # require email verify
            user.save()
            send_verification_email(user)
            messages.info(request, "Check your email to verify your account.")
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user is None:
        messages.error(request, "Invalid activation link.")
        return render(request, "registration/activation_invalid.html", status=400)

    if user.is_active:
        messages.info(request, "Your account is already active. You can log in.")
        return redirect("login")

    if activation_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)  # instantly log them in
        messages.success(request, "Your account is confirmed. Welcome!")
        return redirect("my_specials")  # or wherever you want to land them
    else:
        # Token is invalid or expired
        return render(request, "registration/activation_invalid.html", status=400)


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified. You can log in now.")
        return redirect("login")

    return HttpResponse("Invalid verification link", status=400)

from .forms import ProfileForm

@login_required
def profile_card(request, profile_id):
    profile = get_object_or_404(UserProfile, pk=profile_id)
    if request.user != profile.user:
        return HttpResponseForbidden()
    if request.GET.get("fragment") == "display":
        return render(request, "profiles/_display.html", {"profile": profile})


@login_required
def profile_edit(request, profile_id):
    profile = get_object_or_404(UserProfile, pk=profile_id)
    if request.user != profile.user:
        return HttpResponseForbidden()
    form = ProfileForm(instance=profile)
    return render(request, "profiles/_form.html", {"profile": profile, "form": form})

@login_required
def profile_save(request, profile_id):
    profile = get_object_or_404(UserProfile, pk=profile_id)
    if request.user != profile.user:
        return HttpResponseForbidden()
    if request.method != "POST":
        # Return display if someone GETs the save URL
        return render(request, "profiles/_display.html", {"profile": profile})

    form = ProfileForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
        # Return the display fragment on success
        return render(request, "profiles/_display.html", {"profile": profile})
    # Return the form with errors if invalid
    return render(request, "profiles/_form.html", {"profile": profile, "form": form}, status=400)