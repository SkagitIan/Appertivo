from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import UserProfile
from unittest.mock import patch


class BillingTests(TestCase):
    """Tests for the billing page and subscription flow."""

    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", password="pass")
        UserProfile.objects.create(user=self.user, restaurant_name="Testaurant")

    def test_billing_page_displays_current_plan(self):
        self.client.login(username="test@example.com", password="pass")
        response = self.client.get(reverse("billing"))
        self.assertContains(response, "Current Plan")
        self.assertContains(response, "Free")
        self.assertContains(response, "Pro")
        self.assertContains(response, "Enterprise")

    @patch("app.views.stripe.Subscription.create")
    def test_subscribe_updates_profile_and_redirects(self, mock_create):
        mock_create.return_value = {"id": "sub_123"}
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("subscribe"), {"plan": "pro"})
        self.assertRedirects(response, reverse("dashboard"))
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.subscription_tier, "pro")

    def test_cancel_subscription_sets_free_tier(self):
        profile = UserProfile.objects.get(user=self.user)
        profile.subscription_tier = "pro"
        profile.save()
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("cancel_subscription"))
        self.assertRedirects(response, reverse("billing"))
        profile.refresh_from_db()
        self.assertEqual(profile.subscription_tier, "free")
