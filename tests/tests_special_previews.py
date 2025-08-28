from django.test import TestCase
from django.urls import reverse

class SpecialPreviewTests(TestCase):
    """Tests for special distribution previews on home page."""

    def test_home_page_shows_platform_previews(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'data-platform="widget"')
        self.assertContains(response, 'data-platform="google"')
        self.assertContains(response, 'data-platform="instagram"')
        self.assertContains(response, 'data-platform="facebook"')
        self.assertContains(response, 'data-platform="x"')
