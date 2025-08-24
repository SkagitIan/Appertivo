from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from app.models import Connection
from app.integrations.google import publish_special
from types import SimpleNamespace
from unittest.mock import patch


class GoogleLoggingTests(TestCase):
    """Tests for logging output during Google special publication."""

    @override_settings(GOOGLE_API_KEY="key")
    @patch("app.integrations.google.requests.post")
    def test_publish_special_emits_logs(self, mock_post):
        user = User.objects.create_user(username="owner", password="pw")
        Connection.objects.create(
            user=user,
            platform="google_business",
            is_connected=True,
            settings={"access_token": "tok", "account_id": "acc", "location_id": "loc"},
        )
        special = SimpleNamespace(
            user=user,
            title="Deal",
            description="Desc",
            cta_url="https://example.com",
            start_date="2024-01-01",
            end_date="2024-01-02",
        )
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "ok"
        with self.assertLogs("app.integrations.google", level="INFO") as cm:
            publish_special(special)
        self.assertTrue(any("Posting special to Google" in m for m in cm.output))
        self.assertTrue(any("Google response 200" in m for m in cm.output))
