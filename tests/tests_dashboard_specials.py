from datetime import timedelta
import re
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from app.models import Special


class DashboardSpecialsTests(TestCase):
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

    def test_dashboard_shows_only_active_specials_and_view_all_button(self):
        active = self._create_special(title="Active")
        self._create_special(status="expired", title="Expired")

        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, active.title)
        self.assertNotContains(response, "Expired")
        self.assertContains(response, reverse("specials_list"))
        self.assertContains(response, "data-testid=\"button-view-all-specials\"")
        self.assertNotContains(response, "data-testid=\"button-view-specials\"")

    def test_dashboard_special_card_matches_list(self):
        special = self._create_special(title="Match")

        dashboard = self.client.get(reverse("dashboard"))
        specials_list = self.client.get(reverse("specials_list"))

        expected = render_to_string(
            "app/partials/special_card.html",
            {"special": special},
            request=dashboard.wsgi_request,
        )
        # remove csrf tokens and collapse whitespace
        expected = re.sub(r"<input[^>]*csrfmiddlewaretoken[^>]*>", "", expected)
        expected = re.sub(r"\s+", " ", expected.strip())

        dash_html = re.sub(
            r"<input[^>]*csrfmiddlewaretoken[^>]*>", "", dashboard.content.decode()
        )
        dash_html = re.sub(r"\s+", " ", dash_html)

        list_html = re.sub(
            r"<input[^>]*csrfmiddlewaretoken[^>]*>", "", specials_list.content.decode()
        )
        list_html = re.sub(r"\s+", " ", list_html)

        self.assertIn(expected, dash_html)
        self.assertIn(expected, list_html)
