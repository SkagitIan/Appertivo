from django.test import TestCase
from django.urls import reverse


class ResourcesPageTests(TestCase):
    """Tests for the resources page and navigation link."""

    def test_resources_page_contains_sections(self):
        response = self.client.get(reverse('resources'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="searchInput"', html=False)
        self.assertContains(response, 'id="searchResults"', html=False)
        self.assertContains(response, 'FAQs')
        self.assertContains(response, 'Articles')

    def test_home_page_links_to_resources(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'href="/resources/"', html=False)
