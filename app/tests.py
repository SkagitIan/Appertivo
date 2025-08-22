import datetime
import json
import re
from unittest.mock import patch
from django.template.loader import render_to_string
from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .forms import SpecialForm
from .models import Special, EmailSignup, Integration
from .integrations import google
from profiles.models import UserProfile


class AllauthTemplateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _render(self, template):
        request = self.factory.get("/")
        return render_to_string(template, request=request)

    def test_account_login_template(self):
        html = self._render("account/login.html")
        self.assertIn("Connecting to Google", html)

    def test_account_signup_template(self):
        html = self._render("account/signup.html")
        self.assertIn("Connecting to Google", html)


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

    def test_ai_enhance_label_present(self):
        html = self.render()
        self.assertIn('AI Enhance', html)

    def test_cta_buttons_present(self):
        html = self.render()
        self.assertIn('data-cta="order"', html)
        self.assertIn('data-cta="call"', html)
        self.assertIn('data-cta="mobile_order"', html)


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
        html = render_to_string("app/dashboard.html", {"specials": []})
        self.assertIn("integration-connections", html)


class SpecialsListTemplateTests(TestCase):
    def render(self, specials):
        for sp in specials:
            if sp.pk is None:
                sp.save()
        return render_to_string("app/partials/specials_list.html", {"specials": specials})

    def test_management_buttons_present(self):
        sp = Special.objects.create(title="Test")
        html = self.render([sp])
        self.assertIn("fa-pen", html)
        self.assertIn("fa-trash", html)

    def test_published_special_has_glow(self):
        live = Special.objects.create(title="Live", published=True)
        draft = Special.objects.create(title="Draft", published=False)
        html = self.render([live, draft])
        self.assertEqual(html.count("special-live"), 1)

    def test_uses_grid_layout(self):
        sp = Special.objects.create(title="Grid")
        html = self.render([sp])
        self.assertIn("row-cols", html)

    def test_shows_expired_label(self):
        sp = Special.objects.create(title="Old", end_date=datetime.date(2024, 1, 1))
        html = self.render([sp])
        self.assertIn("Expired", html)

    def test_shows_active_label(self):
        sp = Special.objects.create(
            title="Fresh",
            end_date=datetime.date.today() + datetime.timedelta(days=1),
        )
        html = self.render([sp])
        self.assertIn("Active", html)

    def test_hides_sold_out_for_expired_special(self):
        sp = Special.objects.create(
            title="Old",
            end_date=datetime.date.today() - datetime.timedelta(days=1),
        )
        html = self.render([sp])
        self.assertNotIn("Sold Out", html)


class SpecialWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")
        self.profile = UserProfile.objects.create(user=self.user)

    def _valid_data(self):
        return {
            "title": "Test",
            "description": "Desc",
            "cta_choices": "order",
            "order_url": "https://example.com",
        }

    def test_create_redirects_to_preview(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("special_create"), self._valid_data())
        self.assertEqual(response.status_code, 302)
        sp = Special.objects.get(title="Test")
        self.assertTrue(response["Location"].endswith(reverse("special_preview", args=[sp.pk])))

    def test_publish_redirects_to_my_specials(self):
        sp = Special.objects.create(
            title="T",
            description="D",
            order_url="https://e.com",
            cta_choices=["order"],
            user_profile=self.profile,
        )
        self.client.force_login(self.user)
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
        self.client.force_login(self.user)
        self.client.post(reverse("special_create"), data)
        self.assertTrue(mock_enhance.called)

    @override_settings(OPENAI_API_KEY="test")
    @patch("app.views.enhance_special_content")
    def test_create_skips_ai_when_disabled(self, mock_enhance):
        data = self._valid_data()
        self.client.force_login(self.user)
        self.client.post(reverse("special_create"), data)
        self.assertFalse(mock_enhance.called)

    def test_get_create_page_displays_form(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("special_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="special-form"')

    def test_dashboard_has_no_create_form(self):
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, 'id="special-form"')



class SpecialPreviewAccessTests(TestCase):
    """Access control for the special preview view."""

    def setUp(self):
        self.profile = UserProfile.objects.create()
        self.special = Special.objects.create(title="T", user_profile=self.profile)

    def test_redirects_anonymous_user_to_signup(self):
        url = reverse("special_preview", args=[self.special.pk])
        response = self.client.get(url)
        signup_url = reverse("signup")
        self.assertRedirects(response, f"{signup_url}?next={url}")

    def test_authenticated_user_sees_embed(self):
        user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(user)
        url = reverse("special_preview", args=[self.special.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="appertivo-preview"', response.content.decode())


class SpecialAnalyticsTests(TestCase):
    def setUp(self):
        self.profile = UserProfile.objects.create()
        self.special = Special.objects.create(title="A", user_profile=self.profile)

    def test_track_open_increments(self):
        url = reverse("track_open", args=[self.special.pk])
        self.client.post(url)
        self.special.refresh_from_db()
        self.assertEqual(self.special.analytics.opens, 1)

    def test_track_cta_increments(self):
        url = reverse("track_cta", args=[self.special.pk])
        self.client.post(url)
        self.special.refresh_from_db()
        self.assertEqual(self.special.analytics.cta_clicks, 1)

    def test_subscribe_increments_email_signups(self):
        url = reverse("subscribe_email")
        payload = {
            "email": "a@example.com",
            "restaurant_id": self.profile.pk,
            "special_id": self.special.pk,
        }
        self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.special.refresh_from_db()
        self.assertEqual(self.special.analytics.email_signups, 1)

    def test_specials_list_shows_stats(self):
        analytics = self.special.analytics
        analytics.opens = 5
        analytics.cta_clicks = 2
        analytics.email_signups = 3
        analytics.save()
        html = render_to_string(
            "app/partials/specials_list.html", {"specials": [self.special]}
        )
        self.assertIn("card-footer", html)
        self.assertIn("5", html)
        self.assertIn("2", html)
        self.assertIn("3", html)


class MySpecialsTemplateTests(TestCase):
    """Tests for the my specials page."""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass")
        self.profile = UserProfile.objects.create(user=self.user)
        self.special1 = Special.objects.create(
            title="A",
            user_profile=self.profile,
        )
        self.special2 = Special.objects.create(
            title="B",
            user_profile=self.profile,
        )
        analytics1 = self.special1.analytics
        analytics1.opens = 3
        analytics1.cta_clicks = 1
        analytics1.email_signups = 2
        analytics1.save()
        analytics2 = self.special2.analytics
        analytics2.opens = 2
        analytics2.cta_clicks = 4
        analytics2.email_signups = 1
        analytics2.save()
        EmailSignup.objects.create(
            user_profile=self.profile,
            email="first@example.com",
        )
        EmailSignup.objects.create(
            user_profile=self.profile,
            email="second@example.com",
        )

    def _get(self):
        self.client.login(username="owner", password="pass")
        return self.client.get(reverse("my_specials"))


    def test_page_includes_specials_list(self):
        response = self._get()
        self.assertContains(response, "A")
        self.assertContains(response, "B")

    def test_page_shows_aggregated_stats(self):
        response = self._get()
        self.assertContains(response, "Total Opens")
        self.assertContains(response, "5")
        self.assertContains(response, "CTA Clicks")
        self.assertContains(response, "5")
        self.assertContains(response, "Email Signups")
        self.assertContains(response, "3")

    def test_page_lists_email_subscribers(self):
        response = self._get()
        self.assertContains(response, "first@example.com")
        self.assertContains(response, "second@example.com")

    def test_page_has_billing_section(self):
        response = self._get()
        self.assertContains(response, "Billing")

    def test_page_shows_active_special_stats(self):
        self.special1.published = True
        self.special1.end_date = timezone.localdate() + timedelta(days=1)
        self.special1.save()
        response = self._get()
        self.assertContains(response, "Active Special")
        self.assertContains(response, self.special1.title)
        self.assertContains(response, "Opens: 3")
        self.assertContains(response, "CTA Clicks: 1")
        self.assertContains(response, "Email Signups: 2")


class IntegrationModelTests(TestCase):
    def test_create_integration(self):
        profile = UserProfile.objects.create()
        Integration.objects.create(user_profile=profile, provider="google", enabled=True)
        self.assertTrue(
            Integration.objects.filter(user_profile=profile, provider="google", enabled=True).exists()
        )


class IntegrationToggleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="pw")
        self.profile = UserProfile.objects.create(user=self.user, is_premium=True)

    def test_toggle_enables_integration(self):
        self.client.force_login(self.user)
        url = reverse("integrations_toggle", args=["google"])
        response = self.client.post(url, {"enabled": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Integration.objects.filter(user_profile=self.profile, provider="google", enabled=True).exists()
        )


class GoogleIntegrationsConnectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="conn", password="pw")
        self.profile = UserProfile.objects.create(user=self.user, is_premium=True)

    @override_settings(GOOGLE_CLIENT_ID="cid", GOOGLE_REDIRECT_URI="https://redir")
    def test_connect_redirects_to_google(self):
        self.client.force_login(self.user)
        url = reverse("integrations_connect", args=["google"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response["Location"])


class GoogleIntegrationTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="temp", password="pw")
        self.profile = UserProfile.objects.create(user=self.user, is_premium=True)

    def _get(self):
        self.client.login(username="temp", password="pw")
        return self.client.get(reverse("my_specials"))

    def test_connect_button_shown_when_not_connected(self):
        response = self._get()
        connect_url = reverse("integrations_connect", args=["google"])
        self.assertContains(response, f'href="{connect_url}"')
        self.assertContains(response, ">Connect<")

    def test_configure_button_when_connected(self):
        Integration.objects.create(user_profile=self.profile, provider="google", enabled=True)
        response = self._get()
        connect_url = reverse("integrations_connect", args=["google"])
        self.assertContains(response, f'href="{connect_url}"')
        self.assertContains(response, "Configure")
        self.assertNotContains(response, ">Connect<")



class GooglePublishTests(TestCase):
    """Tests for posting specials to Google Business Profile."""

    def setUp(self):
        self.user = User.objects.create_user(username="gpub", password="pw")
        self.profile = UserProfile.objects.create(user=self.user)
        self.special = Special.objects.create(
            title="Title",
            description="Desc",
            user_profile=self.profile,
            order_url="https://example.com",
        )

    @override_settings(GOOGLE_API_KEY="key")
    @patch("app.integrations.google.requests.post")
    def test_publish_special_posts_offer(self, mock_post):
        Integration.objects.create(
            user_profile=self.profile,
            provider="google",
            enabled=True,
            access_token="tok",
            account_id="acc",
            location_id="loc",
        )
        google.publish_special(self.special)
        self.assertTrue(mock_post.called)
        url = mock_post.call_args[0][0]
        self.assertIn("accounts/acc/locations/loc/localPosts", url)

    @override_settings(GOOGLE_CLIENT_ID="cid", GOOGLE_REDIRECT_URI="https://redir")
    @patch("app.integrations.google.publish_special")
    def test_special_publish_triggers_google(self, mock_publish):
        self.client.force_login(self.user)
        Integration.objects.create(
            user_profile=self.profile,
            provider="google",
            enabled=True,
            access_token="tok",
            account_id="acc",
            location_id="loc",
        )
        response = self.client.post(reverse("special_publish", args=[self.special.pk]))
        self.assertEqual(response.status_code, 302)
        mock_publish.assert_called_once_with(self.special)



