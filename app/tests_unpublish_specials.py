from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from app.models import Special, Connection
from app import cron, distribution


class UnpublishSpecialsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")

    def _create_special(self, **kwargs):
        defaults = dict(
            user=self.user,
            title="Deal",
            description="Desc",
            price=10,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
            status="active",
        )
        defaults.update(kwargs)
        return Special.objects.create(**defaults)

    @patch("app.distribution.remove_special_from_distributions")
    def test_unpublish_expired_specials(self, mock_remove):
        expired = self._create_special()
        active = self._create_special(end_date=timezone.now() + timedelta(days=1))

        cron.unpublish_expired_specials()

        expired.refresh_from_db()
        active.refresh_from_db()

        self.assertEqual(expired.status, "expired")
        self.assertEqual(active.status, "active")
        mock_remove.assert_called_once_with(expired)

    @patch("app.integrations.google.remove_special")
    def test_remove_special_from_distributions_invokes_google(self, mock_google):
        special = self._create_special(google_post_name="accounts/1/locations/2/localPosts/3")
        Connection.objects.create(
            user=self.user,
            platform="google_business",
            is_connected=True,
            settings={"access_token": "tok", "account_id": "1", "location_id": "2"},
        )

        distribution.remove_special_from_distributions(special)
        mock_google.assert_called_once()
