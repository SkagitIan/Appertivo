from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from profiles.models import UserProfile


class SettingsModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="modaluser", password="pw")
        UserProfile.objects.create(user=self.user)

    def test_settings_icon_and_modal_present(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, 'data-bs-target="#settingsModal"')
        self.assertContains(response, 'id="settingsModal"')
        self.assertContains(response, "Profile")
        self.assertContains(response, "Stats")
        self.assertContains(response, "Billing")
        self.assertContains(response, "Integrations")
