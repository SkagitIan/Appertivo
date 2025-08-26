from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import Connection

class DashboardLocationModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="modaluser", password="pw")

    def test_modal_rendered_when_no_location(self):
        Connection.objects.create(
            user=self.user,
            platform="google_business",
            is_connected=True,
            settings={
                "access_token": "tok",
                "account_id": "acc",
                "locations": [{"id": "1", "name": "Loc1"}],
            },
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Select a Location")
        self.assertContains(response, "Loc1")
        self.assertContains(response, 'name="location_id"')

    def test_no_modal_when_location_selected(self):
        Connection.objects.create(
            user=self.user,
            platform="google_business",
            is_connected=True,
            settings={
                "access_token": "tok",
                "account_id": "acc",
                "location_id": "1",
                "locations": [{"id": "1", "name": "Loc1"}],
            },
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "Select a Location")
