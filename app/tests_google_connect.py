from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import Connection
from unittest.mock import patch, Mock

class GoogleConnectionFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")
        Connection.objects.create(user=self.user, platform="google_business")

    @override_settings(GOOGLE_CLIENT_ID="cid", GOOGLE_REDIRECT_URI="https://redir")
    def test_connect_redirects_to_google(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("google_connect"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])

    @override_settings(GOOGLE_CLIENT_ID="cid", GOOGLE_CLIENT_SECRET="sec", GOOGLE_REDIRECT_URI="https://redir")
    @patch("app.integrations.google.requests.get")
    @patch("app.integrations.google.requests.post")
    def test_callback_marks_connection(self, mock_post, mock_get):
        mock_post.return_value.json.return_value = {"access_token": "tok", "refresh_token": "ref"}
        mock_get.side_effect = [
            Mock(json=lambda: {"accounts": [{"name": "accounts/123"}]}),
            Mock(json=lambda: {"locations": [{"name": "accounts/123/locations/456"}]})
        ]
        self.client.force_login(self.user)
        response = self.client.get(reverse("google_callback"), {"code": "abc"})
        self.assertEqual(response.status_code, 302)
        conn = Connection.objects.get(user=self.user, platform="google_business")
        self.assertTrue(conn.is_connected)
        self.assertEqual(conn.settings["account_id"], "123")
        self.assertEqual(conn.settings["location_id"], "456")
    @override_settings(GOOGLE_API_KEY="key")
    @patch("app.integrations.google.requests.post")
    @patch("app.views.send_special_notification")
    def test_creating_special_posts_to_google(self, mock_notify, mock_post):
        self.client.force_login(self.user)
        conn = Connection.objects.get(user=self.user, platform="google_business")
        conn.is_connected = True
        conn.settings = {"access_token": "tok", "account_id": "acc", "location_id": "loc"}
        conn.save()
        data = {
            "title": "Deal",
            "description": "Desc",
            "price": "5.00",
            "start_date": "2024-01-01T00:00",
            "end_date": "2024-01-02T00:00",
            "cta_type": "web",
            "cta_url": "https://example.com",
        }
        response = self.client.post(reverse("create_special"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_post.called)
