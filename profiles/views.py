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
    """Handle user signup."""

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user, defaults={"email": user.email})
            from .emails import send_verification_email

            send_verification_email(user)
            messages.info(request, "Check your email to verify your account.")
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


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


@login_required
def profile_view(request):
    profile = request.user.userprofile
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
