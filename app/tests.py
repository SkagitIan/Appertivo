from django.template.loader import render_to_string
from django.test import TestCase

from .forms import SpecialForm


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

    def test_cta_groups_present(self):
        html = self.render()
        self.assertIn('id="group-order"', html)
        self.assertIn('id="group-mobile"', html)
        self.assertIn('id="group-call"', html)

    def test_date_inputs_visually_hidden(self):
        html = self.render()
        self.assertIn('id="id_start_date"', html)
        self.assertIn('visually-hidden', html)

    def test_js_bindings_exist(self):
        html = self.render()
        self.assertTrue('function bindPrice' in html)
        self.assertEqual(html.count('function bindCTA'), 1)
