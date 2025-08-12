import datetime
import re
from unittest.mock import patch
from django.template.loader import render_to_string
from django.test import TestCase, override_settings
from django.urls import reverse
from .forms import SpecialForm
from .models import Special
from profiles.models import UserProfile


class SpecialFormTemplateTests(TestCase):
    def render(self):
        form = SpecialForm()
        return render_to_string("app/partials/special_form.html", {"form": form})

    def test_price_field_rendered(self):
        html = self.render()
        self.assertIn('id="id_price"', html)
        self.assertIn('inputmode="decimal"', html)

    def test_date_buttons_present(self):
        html = self.render()
        self.assertTrue('id="start-date-button"' in html)
        self.assertTrue('id="end-date-button"' in html)
        self.assertTrue('id="id_start_date"' in html)
        self.assertTrue('id="id_end_date"' in html)

    def test_image_input_present(self):
        html = self.render()
        self.assertTrue('id="id_image"' in html)
        self.assertTrue('type="file"' in html)

    def test_js_bindings_exist(self):
        html = self.render()
        self.assertTrue('function bindPrice' in html)
        self.assertEqual(html.count('function bindCTA'), 1)

    def test_date_inputs_not_display_none(self):
        html = self.render()
        self.assertNotIn('d-none" id="id_start_date"', html)
        self.assertNotIn('d-none" id="id_end_date"', html)

    def test_no_card_footer(self):
        html = self.render()
        self.assertNotIn('card-footer', html)

    def test_cta_radio_checked_with_list_value(self):
        profile = UserProfile.objects.create()
        sp = Special(
            title="T",
            description="D",
            order_url="https://e.com",
            cta_choices=["order"],
            user_profile=profile,
        )
        form = SpecialForm(instance=sp)
        html = render_to_string("app/partials/special_form.html", {"form": form, "special": sp})
        self.assertIsNotNone(re.search(r'id="cta_1"[^>]*value="order"[^>]*checked', html))

    def test_existing_image_shown_inside_dropzone(self):
        profile = UserProfile.objects.create()
        sp = Special(
            title="T",
            description="D",
            order_url="https://e.com",
            cta_choices=["order"],
            image="https://img.example/test.jpg",
            user_profile=profile,
        )
        form = SpecialForm(instance=sp)
        html = render_to_string("app/partials/special_form.html", {"form": form, "special": sp})
        self.assertIsNotNone(re.search(r'id="image-preview"[^>]*src="https://img.example/test.jpg"', html))
        self.assertNotIn('d-none" id="image-preview"', html)

    def test_ai_enhance_switch_present_and_checked(self):
        html = self.render()
        self.assertIn('id="id_ai_enhance"', html)
        self.assertIsNotNone(re.search(r'id="id_ai_enhance"[^>]*checked', html))


class ConnectionPartialTests(TestCase):
    def render(self):
        return render_to_string("app/partials/connection.html")

    def test_buttons_present(self):
        html = self.render()
        platforms = [
            "DoorDash",
            "Grubhub",
            "Wix",
            "Uber Eats",
            "WordPress",
            "Squarespace",
            "Webflow",
        ]
        for name in platforms:
            self.assertIn(name, html)

    def test_button_order(self):
        html = self.render()
        order = [
            html.index("DoorDash"),
            html.index("Grubhub"),
            html.index("Wix"),
            html.index("Uber Eats"),
            html.index("WordPress"),
            html.index("Squarespace"),
            html.index("Webflow"),
        ]
        self.assertEqual(order, sorted(order))


class DashboardTemplateTests(TestCase):
    def test_connections_partial_included(self):
        html = render_to_string("app/dashboard.html", {"specials": [], "form": None})
        self.assertIn("integration-connections", html)


class SpecialsListTemplateTests(TestCase):
    def render(self, specials):
        return render_to_string("app/partials/specials_list.html", {"specials": specials})

    def test_management_buttons_present(self):
        sp = Special(title="Test")
        html = self.render([sp])
        self.assertIn("bi-pencil", html)
        self.assertIn("bi-x-lg", html)
        self.assertIn("Sold Out", html)
        self.assertIn("Make Active", html)

    def test_published_special_has_glow(self):
        live = Special(title="Live", published=True)
        draft = Special(title="Draft", published=False)
        html = self.render([live, draft])
        self.assertEqual(html.count("special-live"), 1)

    def test_uses_grid_layout(self):
        sp = Special(title="Grid")
        html = self.render([sp])
        self.assertIn("row-cols", html)

    def test_shows_expired_label(self):
        sp = Special(title="Old", end_date=datetime.date(2024, 1, 1))
        html = self.render([sp])
        self.assertIn("Expired:", html)


class SpecialWorkflowTests(TestCase):
    def _valid_data(self):
        return {
            "title": "Test",
            "description": "Desc",
            "cta_choices": "order",
            "order_url": "https://example.com",
        }

    def test_create_redirects_to_preview(self):
        response = self.client.post(reverse("special_create"), self._valid_data())
        self.assertEqual(response.status_code, 302)
        sp = Special.objects.get(title="Test")
        self.assertRedirects(response, reverse("special_preview", args=[sp.pk]))

    def test_publish_redirects_to_my_specials(self):
        profile = UserProfile.objects.create()
        sp = Special.objects.create(
            title="T",
            description="D",
            order_url="https://e.com",
            cta_choices=["order"],
            user_profile=profile,
        )
        response = self.client.post(reverse("special_publish", args=[sp.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith(reverse("my_specials")))
        sp.refresh_from_db()
        self.assertTrue(sp.published)

    @override_settings(OPENAI_API_KEY="test")
    @patch("app.views.enhance_special_content")
    def test_create_calls_ai_when_enabled(self, mock_enhance):
        data = self._valid_data()
        data["ai_enhance"] = "on"
        self.client.post(reverse("special_create"), data)
        self.assertTrue(mock_enhance.called)

    @override_settings(OPENAI_API_KEY="test")
    @patch("app.views.enhance_special_content")
    def test_create_skips_ai_when_disabled(self, mock_enhance):
        data = self._valid_data()
        self.client.post(reverse("special_create"), data)
        self.assertFalse(mock_enhance.called)



