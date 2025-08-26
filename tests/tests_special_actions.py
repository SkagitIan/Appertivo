from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.test import TestCase

from app.models import Special


class SpecialsListActionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")
        self.client.login(username="owner", password="pw")

    def _create_special(self, **kwargs):
        defaults = dict(
            user=self.user,
            title="Deal",
            description="Desc",
            price="10.00",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            status="active",
            cta_type="web",
            cta_url="",
            cta_phone="",
        )
        defaults.update(kwargs)
        return Special.objects.create(**defaults)

    def test_image_and_button_text(self):
        image = SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")
        special_with_image = self._create_special(image=image)
        self._create_special(status="expired", title="Old")

        response = self.client.get(reverse("specials_list"))
        self.assertContains(response, "Sold Out")
        self.assertContains(response, "Publish")
        self.assertContains(response, special_with_image.image.url)

    def test_publish_and_unpublish(self):
        active = self._create_special()
        expired = self._create_special(status="expired", title="Old")

        self.client.post(reverse("special_unpublish", args=[active.id]))
        active.refresh_from_db()
        self.assertEqual(active.status, "expired")

        self.client.post(reverse("special_publish", args=[expired.id]))
        expired.refresh_from_db()
        self.assertEqual(expired.status, "active")

    def test_edit_special(self):
        special = self._create_special(title="Old")
        data = {
            "title": "New",
            "description": special.description,
            "price": special.price,
            "start_date": special.start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": special.end_date.strftime("%Y-%m-%d %H:%M:%S"),
            "cta_type": special.cta_type,
            "cta_url": special.cta_url,
            "cta_phone": special.cta_phone,
        }
        self.client.post(reverse("special_edit", args=[special.id]), data)
        special.refresh_from_db()
        self.assertEqual(special.title, "New")

    def test_delete_special(self):
        special = self._create_special()
        self.client.post(reverse("special_delete", args=[special.id]))
        self.assertFalse(Special.objects.filter(id=special.id).exists())
