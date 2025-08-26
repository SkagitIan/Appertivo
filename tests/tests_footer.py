from django.test import TestCase
from django.urls import reverse


class HomeFooterTests(TestCase):
    """Tests for the footer content on the home page."""

    def test_footer_contains_navigation_and_info(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, '<footer', html=False)
        for href in ['href="/"', 'href="/register/"', 'href="/login/"',
                     'href="/dashboard/"', 'href="/specials/"',
                     'href="/specials/create/"', 'href="/connections/"']:
            with self.subTest(href=href):
                self.assertContains(response, href, html=False)
        self.assertContains(response, 'Future Articles')
        self.assertContains(response, 'Appertivo Inc.')
        self.assertContains(response, '123 Food St')
        for social in ['https://facebook.com', 'https://x.com', 'https://instagram.com']:
            with self.subTest(social=social):
                self.assertContains(response, social)
