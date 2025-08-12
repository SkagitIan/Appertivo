from django.template.loader import render_to_string
from django.test import TestCase

from .forms import SpecialForm
from .models import Special


class SpecialFormTemplateTests(TestCase):
    def render(self):
        form = SpecialForm()
        return render_to_string("app/partials/special_form.html", {"form": form})

    def test_price_field_rendered(self):
        html = self.render()
        self.assertTrue('id="id_price"' in html)
        self.assertTrue('type="number"' in html)

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
        self.assertIn("Delete", html)
        self.assertIn("Sold Out", html)
        self.assertIn("Make Active", html)
        self.assertIn("Edit", html)

    def test_published_special_has_glow(self):
        live = Special(title="Live", published=True)
        draft = Special(title="Draft", published=False)
        html = self.render([live, draft])
        self.assertEqual(html.count("special-live"), 1)

    def test_uses_grid_layout(self):
        sp = Special(title="Grid")
        html = self.render([sp])
        self.assertIn("row-cols", html)

