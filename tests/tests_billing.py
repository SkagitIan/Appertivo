from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from app.models import UserProfile


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

    @patch("app.views.stripe.Price.list")
    @patch("app.views.stripe.Customer.create")
    @patch("app.views.stripe.Customer.modify")
    @patch("app.views.stripe.PaymentMethod.attach")
    @patch("app.views.stripe.Subscription.create")
    def test_subscribe_updates_profile_and_redirects(
        self,
        mock_sub_create,
        mock_pm_attach,
        mock_cust_modify,
        mock_customer_create,
        mock_price_list,
    ):
        mock_sub_create.return_value = {"id": "sub_123"}
        mock_customer_create.return_value = {"id": "cus_123"}
        mock_price_list.return_value = {"data": [{"id": "price_123"}]}
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(
            reverse("subscribe"), {"plan": "pro", "payment_method": "pm_123"}
        )
        self.assertRedirects(response, reverse("dashboard"))
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.subscription_tier, "pro")
        mock_pm_attach.assert_called_once_with("pm_123", customer="cus_123")
        mock_cust_modify.assert_called_once_with(
            "cus_123", invoice_settings={"default_payment_method": "pm_123"}
        )
        mock_sub_create.assert_called_once_with(
            customer="cus_123",
            items=[{"price": "price_123"}],
            default_payment_method="pm_123",
        )

    def test_cancel_subscription_sets_free_tier(self):
        profile = UserProfile.objects.get(user=self.user)
        profile.subscription_tier = "pro"
        profile.save()
        self.client.login(username="test@example.com", password="pass")
        response = self.client.post(reverse("cancel_subscription"))
        self.assertRedirects(response, reverse("billing"))
        profile.refresh_from_db()
        self.assertEqual(profile.subscription_tier, "free")
