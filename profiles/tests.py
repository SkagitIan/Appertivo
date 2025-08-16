from django.core import mail
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase, override_settings


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


class EmailLoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="login@example.com", email="login@example.com", password="password123"
        )

    def test_next_query_parameter_redirects(self):
        next_url = reverse("profile")
        response = self.client.post(
            f"{reverse('login')}?next={next_url}",
            {"username": "login@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_login_template_is_minimal(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "navbar")
