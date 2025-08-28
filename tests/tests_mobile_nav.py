"""Tests for mobile navigation menu on the home page."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class MobileNavigationTests(TestCase):
    """Ensure the mobile menu appears with expected links."""

    def test_mobile_menu_contains_links_for_anonymous_user(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'id="mobile-menu-button"', html=False)
        self.assertContains(response, 'id="mobile-menu"', html=False)
        self.assertContains(response, reverse('resources'))
        self.assertContains(response, '#pricing')
        self.assertContains(response, reverse('login'))
        self.assertContains(response, reverse('register'))

    def test_mobile_menu_shows_logout_for_authenticated_user(self):
        User = get_user_model()
        User.objects.create_user(username="tester", password="pass123")
        self.client.login(username="tester", password="pass123")
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('logout'))
