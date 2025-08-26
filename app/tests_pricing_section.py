"""Tests for pricing section on the home page."""

from django.test import TestCase
from django.urls import reverse


class HomePricingSectionTests(TestCase):
    """Verify that the home page shows pricing plans and features."""

    def test_home_page_displays_pricing_plans(self):
        response = self.client.get(reverse('home'))
        for plan in ["Free", "Pro", "Enterprise"]:
            with self.subTest(plan=plan):
                self.assertContains(response, plan)
        for feature in [
            "Website widget",
            "Email capture",
            "Post to Google Business Profile",
            "Delivery App Integration",
            "POS Integrations",
            "All features for multiple restaurants",
        ]:
            with self.subTest(feature=feature):
                self.assertContains(response, feature)
