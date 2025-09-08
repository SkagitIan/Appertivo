from django.test import TestCase
from django.urls import reverse


class IdeaPartialTests(TestCase):
    """Tests for the idea partial and menu suggestions endpoint."""

    def test_menu_suggestions_returns_ten_items(self):
        response = self.client.get(
            reverse("menu_suggestions"), {"concept": "Italian"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<li", count=10)

    def test_home_shows_idea_grid(self):
        response = self.client.get(reverse("home"), follow=True)
        self.assertContains(response, "Italian")
        self.assertContains(response, "hx-get", count=9)
