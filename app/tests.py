from django.test import TestCase
from django.urls import reverse
from .models import Special

class SpecialWorkflowTests(TestCase):
    def test_create_redirects_to_preview(self):
        data = {
            'title': 'Test',
            'description': 'Desc',
            'cta_choices': 'order',
            'order_url': 'http://example.com'
        }
        response = self.client.post(reverse('special_create'), data)
        self.assertEqual(Special.objects.count(), 1)
        special = Special.objects.first()
        self.assertRedirects(response, reverse('special_preview', args=[special.pk]))

    def test_publish_sets_published(self):
        sp = Special.objects.create(title='T', description='D', cta_choices=['order'], order_url='http://e.com')
        response = self.client.post(reverse('special_publish', args=[sp.pk]))
        sp.refresh_from_db()
        self.assertTrue(sp.published)
        self.assertRedirects(response, reverse('my_specials'))
