from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from app.models import UserProfile, Subscription, Transaction


class BillingTests(TestCase):
    """Tests for the billing page and subscription flow."""

    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass")
        UserProfile.objects.create(user=self.user, restaurant_name="Testaurant")

    def test_billing_page_shows_subscription_and_transactions(self):
        sub = Subscription.objects.create(user=self.user, stripe_subscription_id="sub_123", plan="pro")
        Transaction.objects.create(subscription=sub, plan="pro", amount=99, status="paid")
        self.client.login(username="test@example.com", password="pass")
        response = self.client.get(reverse("billing"))
        self.assertContains(response, "Current Plan")
        self.assertContains(response, "Pro")
        self.assertContains(response, "$99")

    @patch("app.views.stripe.checkout.Session.create")
    @patch("app.views.stripe.Customer.create")
    def test_subscribe_creates_checkout_session_and_redirects(self, mock_customer_create, mock_session_create):
        """Successful subscribe should create a Stripe Checkout session and redirect."""
        mock_customer_create.return_value = {"id": "cus_123"}
        mock_session_create.return_value = type("obj", (), {"url": "https://stripe.test/session"})()
        self.client.login(username="test@example.com", password="pass")
        with patch("app.views.PRICE_IDS", {"pro": "price_123"}):
            response = self.client.post(reverse("subscribe"), {"plan": "pro"})

        mock_session_create.assert_called_once()
        args, kwargs = mock_session_create.call_args
        self.assertEqual(kwargs["customer"], "cus_123")
        self.assertEqual(kwargs["mode"], "subscription")
        self.assertEqual(kwargs["line_items"], [{"price": "price_123", "quantity": 1}])
        self.assertRedirects(response, "https://stripe.test/session", fetch_redirect_response=False)

    def test_subscribe_with_invalid_plan_redirects_to_billing(self):
        """Posting an invalid plan should redirect back to billing."""
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("subscribe"), {"plan": "invalid"})
        self.assertRedirects(response, reverse("billing"))

    @patch("app.views.stripe.Subscription.delete")
    def test_cancel_subscription_sets_free_tier_and_records_cancel(self, mock_delete):
        profile = UserProfile.objects.get(user=self.user)
        profile.subscription_tier = "pro"
        profile.save()
        sub = Subscription.objects.create(user=self.user, stripe_subscription_id="sub_123", plan="pro")
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("cancel_subscription"))
        self.assertRedirects(response, reverse("billing"))
        profile.refresh_from_db()
        self.assertEqual(profile.subscription_tier, "free")
        sub.refresh_from_db()
        self.assertIsNotNone(sub.canceled_at)
