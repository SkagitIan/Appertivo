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

    @patch("app.views.stripe.Price.list")
    @patch("app.views.stripe.Customer.create")
    @patch("app.views.stripe.Subscription.create")
    def test_subscribe_creates_subscription_and_transaction(self, mock_sub_create, mock_customer_create, mock_price_list):
        mock_sub_create.return_value = {"id": "sub_123"}
        mock_customer_create.return_value = {"id": "cus_123"}
        mock_price_list.return_value = {"data": [{"id": "price_123"}]}
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("subscribe"), {"plan": "pro"})
        self.assertRedirects(response, reverse("dashboard"))
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.subscription_tier, "pro")
        self.assertEqual(profile.stripe_customer_id, "cus_123")
        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.plan, "pro")
        self.assertIsNone(sub.canceled_at)
        tx = Transaction.objects.get(subscription=sub)
        self.assertEqual(tx.amount, 99)
        self.assertEqual(tx.plan, "pro")

    @patch("app.views.stripe.Price.list")
    @patch("app.views.stripe.Customer.create")
    @patch("app.views.stripe.Subscription.create")
    def test_subscribe_uses_stripe_customer_id(self, mock_sub_create, mock_customer_create, mock_price_list):
        mock_price_list.return_value = {"data": [{"id": "price_123"}]}
        mock_customer_create.return_value = {"id": "cus_123"}
        mock_sub_create.return_value = {"id": "sub_123"}

        self.client.login(username="test@example.com", password="pass")
        self.client.post(reverse("subscribe"), {"plan": "pro"})

        mock_customer_create.assert_called_once_with(email="test@example.com")
        mock_sub_create.assert_called_once_with(customer="cus_123", items=[{"price": "price_123"}])
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.stripe_customer_id, "cus_123")

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
