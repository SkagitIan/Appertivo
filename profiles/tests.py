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


class AnonymousProfileMiddlewareTests(TestCase):
    """Tests for the anonymous profile middleware behaviour."""

    def test_profile_created_only_for_special_flow(self):
        """Profile is created only when hitting the special creation flow."""
        # Visiting a non-special page should not create a profile
        self.client.get(reverse("dashboard"))
        self.assertEqual(UserProfile.objects.count(), 0)

        # Visiting the special creation page should create a profile
        response = self.client.get(reverse("special_create"))
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertIn("anonymous_token", response.cookies)

        token = response.cookies["anonymous_token"].value

        # Subsequent non-special requests reuse the existing profile
        response = self.client.get(reverse("dashboard"), HTTP_X_ANONYMOUS_TOKEN=token)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertIn("anonymous_token", response.cookies)
        self.assertEqual(response.cookies["anonymous_token"].value, token)


class SignupAssociatesProfileTests(TestCase):
    """Ensure signup links an anonymous profile with the new user."""

    def test_signup_associates_existing_profile(self):
        # Start the special creation flow to obtain an anonymous profile
        response = self.client.get(reverse("special_create"))
        token = response.cookies["anonymous_token"].value

        # Sign up using the same client (which retains cookies)
        response = self.client.post(
            reverse("signup"),
            {
                "email": "anon@example.com",
                "password1": "complexpass123",
                "password2": "complexpass123",
            },
        )
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="anon@example.com")
        profile = UserProfile.objects.get(anonymous_token=token)
        self.assertEqual(profile.user, user)


class PruneOrphanedProfilesCommandTests(TestCase):
    """Tests for the management command that prunes orphaned profiles."""

    def test_prunes_old_orphan_profiles(self):
        old_profile = UserProfile.objects.create()
        UserProfile.objects.filter(pk=old_profile.pk).update(
            created_at=timezone.now() - timedelta(days=40)
        )

        active_profile = UserProfile.objects.create()
        Special.objects.create(
            user_profile=active_profile,
            title="Test",
            description="Desc",
        )

        call_command("prune_orphaned_profiles", days=30)

        self.assertFalse(UserProfile.objects.filter(pk=old_profile.pk).exists())
        self.assertTrue(UserProfile.objects.filter(pk=active_profile.pk).exists())
