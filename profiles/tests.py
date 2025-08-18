from datetime import timedelta

from django.core import mail
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase, override_settings

from app.models import Special
from profiles.models import UserProfile


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SignupEmailTests(TestCase):
    def test_signup_sends_verification_email(self):
        response = self.client.post(
            reverse("signup"),
            {
                "email": "new@example.com",
                "password1": "complexpass123",
                "password2": "complexpass123",
            },
        )
        # User should be redirected after signup
        self.assertEqual(response.status_code, 302)

        # A user object should be created but inactive until verified
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.is_active)

        # Verification email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].body)


class SocialLoginButtonTests(TestCase):
    def test_login_page_contains_social_buttons(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "/accounts/google/login/")
        self.assertContains(response, "/accounts/apple/login/")

    def test_signup_page_contains_social_buttons(self):
        response = self.client.get(reverse("signup"))
        self.assertContains(response, "/accounts/google/login/")
        self.assertContains(response, "/accounts/apple/login/")
